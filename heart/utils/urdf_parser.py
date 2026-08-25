"""
URDF Parser — Robot Specification Extraction

Parses robot URDF files into structured capability specifications used by
the feasibility and capability reasoning agents. Extracts:
- Gripper: max/min opening, force range, number of grippers/fingers
- Arm: max reach, degrees of freedom, workspace height, number of arms
- Base: footprint, torso lift, mobility type (wheeled/legged/aerial)
- Payload: max weight, joint torque limits

Supports multiple robot types (Fetch, JR2/Kinova, Quadrotor) using
name-agnostic heuristics based on kinematic topology and joint properties.
"""

from __future__ import annotations
import os, re, math, xml.etree.ElementTree as ET
from typing import Dict, Any, List, Tuple
from collections import defaultdict, deque

# ---------- low-level utils ----------

def _strip_ns(root: ET.Element) -> ET.Element:
    for el in root.iter():
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]
    return root

def _get_attr(el: ET.Element, name: str, default=None):
    return el.attrib.get(name, default) if el is not None else default

def _parse_origin(el: ET.Element) -> Tuple[List[float], List[float]]:
    xyz = [0.0, 0.0, 0.0]; rpy = [0.0, 0.0, 0.0]
    if el is None: return xyz, rpy
    if 'xyz' in el.attrib:
        xyz = [float(x) for x in el.attrib['xyz'].split()]
    if 'rpy' in el.attrib:
        rpy = [float(x) for x in el.attrib['rpy'].split()]
    return xyz, rpy

def _rpy_to_R(r, p, y):
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    Rz = [[cy,-sy,0],[sy,cy,0],[0,0,1]]
    Ry = [[cp,0,sp],[0,1,0],[-sp,0,cp]]
    Rx = [[1,0,0],[0,cr,-sr],[0,sr,cr]]
    def dot(A,B): return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return dot(dot(Rz,Ry),Rx)

def _compose(T1, T2):
    R1,t1 = T1; R2,t2 = T2
    R = [[sum(R1[i][k]*R2[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    t = [sum(R1[i][k]*t2[k] for k in range(3)) + t1[i] for i in range(3)]
    return (R,t)

def _T_from_origin(xyz, rpy): return (_rpy_to_R(*rpy), xyz)
def _norm(v): return math.sqrt(sum(x*x for x in v))

# ---------- graph builder ----------

class URDFModel:
    def __init__(self, root: ET.Element):
        self.root = root
        self.name = _get_attr(root, 'name', 'unknown_robot')
        self.links: Dict[str, ET.Element] = {}
        self.joints: Dict[str, ET.Element] = {}
        self.children = defaultdict(list)   # parent_link -> [(child_link, joint_name)]
        self.parents: Dict[str, Tuple[str,str]] = {}  # child_link -> (parent_link, joint_name)
        self._index()

    def _index(self):
        for link in self.root.findall('link'):
            self.links[link.attrib['name']] = link
        for joint in self.root.findall('joint'):
            jn = joint.attrib['name']
            self.joints[jn] = joint
            parent = joint.find('parent').attrib['link']
            child  = joint.find('child').attrib['link']
            self.children[parent].append((child, jn))
            self.parents[child] = (parent, jn)
        self.root_links = [ln for ln in self.links if ln not in self.parents]

    def choose_base(self) -> str:
        # prefer base_footprint > base_link > first root
        for cand in ('base_footprint','base_link'):
            if cand in self.links: return cand
        return self.root_links[0] if self.root_links else list(self.links.keys())[0]

    def static_poses(self, base_link: str|None=None):
        base = base_link or self.choose_base()
        I = [[1,0,0],[0,1,0],[0,0,1]]
        T = {base: (I, [0.0,0.0,0.0])}
        q = deque([base])
        while q:
            cur = q.popleft()
            for child, jn in self.children.get(cur, []):
                j = self.joints[jn]
                xyz, rpy = _parse_origin(j.find('origin'))
                T[child] = _compose(T[cur], _T_from_origin(xyz, rpy))
                q.append(child)
        return T, base

# ---------- detectors (name-agnostic first, names as soft hints) ----------

def _detect_mobility(model: URDFModel) -> Tuple[str,bool,float|None]:
    """Return (mobility_type, has_mobility, max_joint_velocity)"""
    wheel_like = []
    rotor_like = []
    leg_like = []
    max_vel = None
    base = model.choose_base()

    for jn,j in model.joints.items():
        jtype = j.attrib.get('type','')
        if jtype == 'fixed': continue
        parent = j.find('parent').attrib['link']
        # velocity
        lim = j.find('limit')
        if lim is not None and 'velocity' in lim.attrib:
            v = float(lim.attrib['velocity'])
            max_vel = v if max_vel is None else max(max_vel, v)
        axis_el = j.find('axis')
        axis = [0,0,0]
        if axis_el is not None and 'xyz' in axis_el.attrib:
            axis = [float(x) for x in axis_el.attrib['xyz'].split()]
        name_l = jn.lower()
        # wheel candidate: revolute/continuous joint near base (within 2 hops)
        if jtype in ('continuous','revolute'):
            depth = 0
            cur = parent
            near_base = (cur == base)
            while cur in model.parents and depth < 2:
                cur, _ = model.parents[cur]
                if cur == base:
                    near_base = True
                    break
                depth += 1
            if near_base and ('wheel' in name_l or 'caster' in name_l or parent == base):
                wheel_like.append(jn)
        # rotor: continuous z-axis joints whose parent is within 2 hops of base
        # (real rotors attach near base; arm joints are deep in kinematic chain)
        if jtype == 'continuous' and abs(axis[2])>0.8:
            depth = 0
            cur = parent
            while cur in model.parents and depth < 2:
                cur, _ = model.parents[cur]
                depth += 1
            if cur == base:
                rotor_like.append(jn)
        # leg joints: hip/knee/ankle keywords
        if any(kw in name_l for kw in ('hip', 'knee', 'ankle')):
            leg_like.append(jn)

    # vote
    if len(rotor_like) >= 4:
        return 'aerial', True, max_vel
    if len(leg_like) >= 4:
        return 'legged', True, max_vel
    if wheel_like:
        return 'wheeled', True, max_vel
    return 'fixed', False, max_vel

def _longest_nonfixed_chain(model: URDFModel, exclude_pred=None) -> List[Tuple[str,str]]:
    """Return child-link/joint sequence from base to end with most movable joints (exclude by predicate)"""
    base = model.choose_base()
    best = []
    stack = [(base, [])]
    while stack:
        node, path = stack.pop()
        children = model.children.get(node, [])
        if not children:
            # leaf
            movable = [jn for (_,jn) in path if model.joints[jn].attrib.get('type')!='fixed'
                       and (exclude_pred is None or not exclude_pred(model.joints[jn]))]
            if len(movable) > sum(1 for _ in best):
                best = path[:]
        else:
            for (child, jn) in children:
                stack.append((child, path + [(child, jn)]))
    # drop fixed & excluded from count; keep full path for reach calc
    return best

def _arm_chain(model: URDFModel) -> List[Tuple[str,str]]:
    # exclude wheels/rotors by simple predicate near base
    base = model.choose_base()
    def exclude(j: ET.Element):
        parent = j.find('parent').attrib['link']
        if parent == base and j.attrib.get('type') in ('revolute','continuous'):
            # likely base mobility joint -> exclude from "arm"
            return True
        return False
    chain = _longest_nonfixed_chain(model, exclude_pred=exclude)
    return chain

def _reach_height(model: URDFModel, chain: List[Tuple[str,str]]) -> float|None:
    """
    Highest point the end-effector can reach, measured from the base frame.

    Taken as the height of the first movable joint in the arm chain (the
    shoulder, or the torso lift when the arm is mounted on a lifting column)
    plus the length of the chain from there to the tip — i.e. the arm fully
    extended upward. Prismatic lift stroke is already part of the chain, so it
    needs no separate term.
    """
    Tmap, base = model.static_poses()
    shoulder_idx = None
    for i, (_, jn) in enumerate(chain):
        if model.joints[jn].attrib.get('type') != 'fixed':
            shoulder_idx = i
            break
    if shoulder_idx is None:
        return None

    shoulder_link = chain[shoulder_idx][0]
    if shoulder_link not in Tmap:
        return None
    shoulder_z = Tmap[shoulder_link][1][2]

    pts = [Tmap[c][1] for c, _ in chain[shoulder_idx:] if c in Tmap]
    if len(pts) < 2:
        return shoulder_z
    segs = [_norm([pts[i+1][k]-pts[i][k] for k in range(3)]) for i in range(len(pts)-1)]
    return shoulder_z + sum(segs)


def _arm_specs(model: URDFModel) -> Dict[str,Any]:
    """
    Detect multiple arms in the robot.
    Returns combined specs and number of arms.
    """
    # Find all potential arm chains (e.g., left_arm, right_arm)
    arm_chains = []
    base = model.choose_base()
    
    # Look for arm-related keywords in joint/link names
    arm_keywords = ['arm', 'shoulder', 'elbow', 'wrist', 'manipulator']
    potential_arm_roots = []
    
    for link_name in model.links:
        if any(kw in link_name.lower() for kw in arm_keywords):
            # Check if this could be an arm root
            if link_name in model.children:
                potential_arm_roots.append(link_name)
    
    # If no arm keywords found, fall back to single longest chain
    if not potential_arm_roots:
        chain = _arm_chain(model)
        dof = sum(1 for _,jn in chain if model.joints[jn].attrib.get('type')!='fixed')
        if dof == 0:
            return {"has_arm": False, "num_arms": 0, "degrees_of_freedom": 0,
                    "max_reach": None, "reach_height": None}
        
        # Calculate reach for single arm
        Tmap, base = model.static_poses()
        pts = []
        if base in Tmap: pts.append(Tmap[base][1])
        for child,_ in chain:
            if child in Tmap: pts.append(Tmap[child][1])
        reach = None; zspan = None
        if len(pts) >= 2:
            segs = [_norm([pts[i+1][k]-pts[i][k] for k in range(3)]) for i in range(len(pts)-1)]
            reach = sum(segs)
            zs = [p[2] for p in pts]
            zspan = [min(zs), max(zs)]
        return {"has_arm": True, "num_arms": 1, "degrees_of_freedom": dof,
                "max_reach": reach, "reach_height": _reach_height(model, chain)}
    
    # Count distinct arms (e.g., left vs right)
    arm_count = 0
    max_reach = None
    total_dof = 0
    
    # Simple heuristic: look for left/right pairs or numbered arms
    left_arms = [r for r in potential_arm_roots if 'left' in r.lower() or '_l_' in r.lower()]
    right_arms = [r for r in potential_arm_roots if 'right' in r.lower() or '_r_' in r.lower()]
    
    if left_arms and right_arms:
        arm_count = 2  # Dual arm robot
    elif left_arms or right_arms:
        arm_count = 1
    else:
        # Check for numbered arms (arm_1, arm_2, etc.)
        numbered = [r for r in potential_arm_roots if re.search(r'arm[_\s]*\d+', r.lower())]
        arm_count = max(len(numbered), 1) if potential_arm_roots else 0
    
    # Use original single arm calculation for specs (take max/best arm)
    chain = _arm_chain(model)
    dof = sum(1 for _,jn in chain if model.joints[jn].attrib.get('type')!='fixed')
    if dof > 0:
        Tmap, base = model.static_poses()
        pts = []
        if base in Tmap: pts.append(Tmap[base][1])
        for child,_ in chain:
            if child in Tmap: pts.append(Tmap[child][1])
        if len(pts) >= 2:
            segs = [_norm([pts[i+1][k]-pts[i][k] for k in range(3)]) for i in range(len(pts)-1)]
            max_reach = sum(segs)
            zs = [p[2] for p in pts]
        total_dof = dof * max(arm_count, 1)  # Multiply DOF by number of arms
    
    return {
        "has_arm": arm_count > 0,
        "num_arms": arm_count,
        "degrees_of_freedom": total_dof,
        "max_reach": max_reach,
        "reach_height": _reach_height(model, chain) if dof > 0 else None
    }

def _finger_length(model: URDFModel, link_name: str) -> float:
    """Walk the chain from a finger link to its tip, summing joint origin offsets."""
    total = 0.0
    cur = link_name
    while True:
        children = model.children.get(cur, [])
        if not children:
            break
        child, jn = children[0]
        origin = model.joints[jn].find('origin')
        if origin is not None and 'xyz' in origin.attrib:
            xyz = [float(x) for x in origin.attrib['xyz'].split()]
            total += _norm(xyz)
        cur = child
    # If no children (leaf), use the link's own collision/visual geometry extent
    if total == 0.0:
        link_el = model.links.get(link_name)
        if link_el is not None:
            for geom_tag in ('collision', 'visual'):
                geom = link_el.find(f'{geom_tag}/geometry')
                if geom is not None:
                    cyl = geom.find('cylinder')
                    box = geom.find('box')
                    if cyl is not None and 'length' in cyl.attrib:
                        total = float(cyl.attrib['length'])
                        break
                    if box is not None and 'size' in box.attrib:
                        dims = [float(x) for x in box.attrib['size'].split()]
                        total = max(dims)
                        break
    return total


def _gripper_specs(model: URDFModel) -> Dict[str,Any]:
    """
    Detect multiple grippers in the robot.
    Name-agnostic cues:
      - two or more small terminal links sharing same parent (palm)
      - joints are prismatic with opposite ±y axes OR revolute with opposite ±x
      - presence of <mimic>
    Fall back to soft name hints ('grip','finger').
    """
    # find leaves and their parents
    leaves = [ln for ln in model.links if ln not in model.children]
    parent_groups = defaultdict(list)
    for leaf in leaves:
        if leaf in model.parents:
            parent, jn = model.parents[leaf]
            parent_groups[parent].append(jn)

    def axis_of(j):
        ax = [0,0,0]
        axe = j.find('axis')
        if axe is not None and 'xyz' in axe.attrib:
            ax = [float(x) for x in axe.attrib['xyz'].split()]
        return ax

    # Track multiple grippers
    grippers_found = []
    
    # evaluate groups as gripper candidates
    for palm, joints in parent_groups.items():
        if len(joints) < 2: continue
        # two jaws?
        axes = [axis_of(model.joints[j]) for j in joints]
        types = [model.joints[j].attrib.get('type') for j in joints]
        mimics = [model.joints[j].find('mimic') is not None for j in joints]
        # opposite axes along y or x (check if difference is large, not sum)
        opp = any(abs(axes[i][1] - axes[j][1])>1.6 or abs(axes[i][0] - axes[j][0])>1.6
                  for i in range(len(axes)) for j in range(i+1,len(axes)))
        if not opp: 
            continue
        # at least prismatic/revolute
        movable = any(t in ('revolute','prismatic','continuous') for t in types)
        if not movable:
            continue
        
        # Found a gripper
        num_fingers = len(joints)
        max_open = None
        min_open = None
        force = None
        
        # opening from prismatic limits if available
        opens = []
        revolute_opens = []
        lowers = []
        for jn in joints:
            jtype = model.joints[jn].attrib.get('type')
            lim = model.joints[jn].find('limit')
            if lim is not None:
                if 'upper' in lim.attrib and jtype == 'prismatic':
                    opens.append(float(lim.attrib['upper']) - float(lim.attrib.get('lower','0.0')))
                elif 'upper' in lim.attrib and jtype == 'revolute':
                    # Revolute finger: estimate opening from angle × finger length
                    angle_range = float(lim.attrib['upper']) - float(lim.attrib.get('lower','0.0'))
                    # Get finger link length from child geometry
                    child_link = model.joints[jn].find('child').attrib['link']
                    finger_len = _finger_length(model, child_link)
                    if finger_len > 0:
                        revolute_opens.append(finger_len * math.sin(min(angle_range, math.pi/2)))
                if 'lower' in lim.attrib:
                    lowers.append(float(lim.attrib['lower']))
                if 'effort' in lim.attrib:
                    eff = float(lim.attrib['effort'])
                    force = max(force or 0.0, eff)
        if opens:
            # total opening ~ sum of two jaw strokes (prismatic)
            max_open = sum(sorted(opens, reverse=True)[:2])
        elif revolute_opens:
            # revolute fingers: opening ~ sum of two finger sweeps
            max_open = sum(sorted(revolute_opens, reverse=True)[:2])
        if lowers:
            min_open = min(lowers)
            
        grippers_found.append({
            "palm": palm,
            "num_fingers": num_fingers,
            "max_opening": max_open,
            "min_opening": min_open,
            "force": force
        })

    # Multi-finger hand detection (e.g., humanoid 5-finger hands)
    if not grippers_found:
        Tmap, _ = model.static_poses()
        # Only consider links that are likely palms: name contains hand/palm/finger keywords,
        # or links that are deep in an arm chain (not base_link or torso-level)
        hand_keywords = ('hand', 'palm', 'gripper', 'effector')
        for link_name in model.links:
            name_l = link_name.lower()
            # Skip base/torso-level links that happen to have many children
            if link_name in model.root_links:
                continue
            # Must contain hand-related keyword OR be a descendant of wrist/elbow
            is_hand_link = any(kw in name_l for kw in hand_keywords)
            if not is_hand_link:
                # Check if any ancestor contains arm-end keywords
                cur = link_name
                depth = 0
                while cur in model.parents and depth < 5:
                    parent, _ = model.parents[cur]
                    if any(kw in parent.lower() for kw in ('wrist', 'hand', 'palm')):
                        is_hand_link = True
                        break
                    cur = parent
                    depth += 1
            if not is_hand_link:
                continue
            child_joints = model.children.get(link_name, [])
            movable = [(c, jn) for c, jn in child_joints
                       if model.joints[jn].attrib.get('type') in ('revolute', 'prismatic', 'continuous')]
            if len(movable) >= 3:
                # Trace each finger chain to its tip (leaf)
                finger_tips = []
                for child, jn in movable:
                    tip = child
                    while model.children.get(tip):
                        tip = model.children[tip][0][0]
                    if tip in Tmap:
                        finger_tips.append(Tmap[tip][1])

                # Max opening = max distance between any two fingertips at zero config
                max_dist = 0.0
                for i in range(len(finger_tips)):
                    for j in range(i+1, len(finger_tips)):
                        d = _norm([finger_tips[i][k] - finger_tips[j][k] for k in range(3)])
                        max_dist = max(max_dist, d)

                force = None
                for _, jn in movable:
                    lim = model.joints[jn].find('limit')
                    if lim is not None and 'effort' in lim.attrib:
                        eff = float(lim.attrib['effort'])
                        force = max(force or 0.0, eff)

                grippers_found.append({
                    "palm": link_name,
                    "num_fingers": len(movable),
                    "max_opening": round(max_dist, 4) if max_dist > 0 else None,
                    "min_opening": 0.0,
                    "force": force
                })

    # If no grippers found via structure, check names and estimate from finger joints
    if not grippers_found:
        txt = (' '.join(model.links.keys()) + ' ' + ' '.join(model.joints.keys())).lower()
        # Look for left/right gripper patterns
        has_left_gripper = re.search(r'(left.*grip|grip.*left|l_.*finger|finger.*_l)', txt)
        has_right_gripper = re.search(r'(right.*grip|grip.*right|r_.*finger|finger.*_r)', txt)
        has_generic_gripper = re.search(r'(grip|finger|pinch|jaw)', txt)

        # Estimate opening from revolute finger joints (applies to all name-fallback cases)
        finger_joints = [(jn, j) for jn, j in model.joints.items()
                         if 'finger' in jn.lower()
                         and j.attrib.get('type') == 'revolute']
        max_open = None
        force = None
        if finger_joints:
            sweeps = []
            for jn, j in finger_joints:
                lim = j.find('limit')
                if lim is not None and 'upper' in lim.attrib:
                    angle = float(lim.attrib['upper']) - float(lim.attrib.get('lower', '0.0'))
                    child_link = j.find('child').attrib['link']
                    flen = _finger_length(model, child_link)
                    if flen > 0:
                        sweeps.append(flen * math.sin(min(angle, math.pi / 2)))
                if lim is not None and 'effort' in lim.attrib:
                    eff = float(lim.attrib['effort'])
                    force = max(force or 0.0, eff)
            if sweeps:
                max_open = sum(sorted(sweeps, reverse=True)[:2])

        if has_generic_gripper:
            grippers_found = [{"palm": "main", "max_opening": max_open, "force": force}]
    
    # Aggregate gripper specs
    num_grippers = len(grippers_found)
    has_gripper = num_grippers > 0
    
    # Take the max/best specs from all grippers
    max_opening = None
    min_opening = None
    force_range = None
    avg_fingers = None
    
    if grippers_found:
        openings = [g.get("max_opening") for g in grippers_found if g.get("max_opening") is not None]
        min_opens = [g.get("min_opening") for g in grippers_found if g.get("min_opening") is not None]
        forces = [g.get("force") for g in grippers_found if g.get("force") is not None]
        finger_counts = [g.get("num_fingers") for g in grippers_found if g.get("num_fingers") is not None]
        
        if openings:
            max_opening = max(openings)  # Best gripper opening
        if min_opens:
            min_opening = min(min_opens)
        if forces:
            force_range = [0.0, max(forces)]
        if finger_counts:
            avg_fingers = sum(finger_counts) // len(finger_counts)  # Average fingers per gripper

    out = {
        "has_gripper": has_gripper, 
        "num_grippers": num_grippers,
        "max_opening": max_opening, 
        "min_opening": min_opening,
        "force_range": force_range
    }
    if avg_fingers is not None: 
        out["num_fingers"] = avg_fingers
    
    return out

def _payload_specs(model: URDFModel) -> Dict[str,Any]:
    torques = {}
    for jn,j in model.joints.items():
        lim = j.find('limit')
        if lim is None or 'effort' not in lim.attrib: continue
        eff = float(lim.attrib['effort'])
        key = jn.lower()
        # bucketize without strict names
        if 'shoulder' in key: torques['shoulder'] = max(eff, torques.get('shoulder',0.0))
        elif 'elbow' in key: torques['elbow'] = max(eff, torques.get('elbow',0.0))
        elif 'wrist' in key: torques['wrist'] = max(eff, torques.get('wrist',0.0))
        elif 'torso' in key and 'lift' in key: torques['torso_lift'] = max(eff, torques.get('torso_lift',0.0))
        else: torques[jn] = eff
    return {"max_weight": None, "max_torque": torques or None}

def _base_specs(model: URDFModel) -> Dict[str,Any]:
    mtype, has_mob, max_vel = _detect_mobility(model)
    # Override for quadrotor/aerial robots that use non-standard propeller tags
    nm = model.name.lower()
    if mtype == 'fixed' and ('quad' in nm or 'rotor' in nm or 'drone' in nm or 'uav' in nm):
        txt = ET.tostring(model.root, encoding='unicode').lower()
        if 'propell' in txt or 'rotor' in txt:
            mtype = 'flying'
            has_mob = True
    # torso stroke
    torso = None
    for jn,j in model.joints.items():
        if 'torso' in jn.lower() and j.attrib.get('type') in ('prismatic','revolute'):
            lim = j.find('limit')
            if lim is not None and 'upper' in lim.attrib:
                upper = float(lim.attrib['upper'])
                lower = float(lim.attrib.get('lower','0.0'))
                torso = (upper - lower)
                break
    # footprint link
    footprint = 'base_footprint' if 'base_footprint' in model.links else ('base_link' if 'base_link' in model.links else (model.root_links[0] if model.root_links else None))
    return {"footprint": footprint, "max_velocity": max_vel, "mobility_type": mtype, "has_mobility": has_mob, "torso_lift": torso}

def _sensor_specs(model: URDFModel) -> Dict[str,Any]:
    txt = ET.tostring(model.root, encoding='unicode').lower()
    has_lidar = any(tag in txt for tag in ['<ray','<gpu_ray','lidar','hokuyo','velodyne','laser'])
    has_cam   = 'camera' in txt or 'rgbd' in txt or 'kinect' in txt or 'optical_frame' in txt or 'eyes' in txt
    has_depth = 'rgbd' in txt or 'depth' in txt or 'kinect' in txt
    # camera height via link pose
    Tmap, base = model.static_poses()
    cam_h = None
    for ln in model.links:
        if re.search(r'(camera|optical|eyes)', ln, re.I):
            if ln in Tmap:
                cam_h = Tmap[ln][1][2]; break
    # horizontal_fov (Gazebo)
    m = re.search(r'horizontal_fov[^>]*>([^<]+)<', txt)
    hfov = float(m.group(1)) if m else None
    return {"has_camera": bool(has_cam), "has_depth": bool(has_depth), "has_lidar": bool(has_lidar),
            "camera_height": cam_h, "camera_fov": hfov}

def _robot_type_guess(model: URDFModel) -> str:
    nm = model.name.lower()
    mtype, has_mob, _ = _detect_mobility(model)
    if 'fetch' in nm: return 'fetch'
    if 'jr2' in nm or 'kinova' in nm: return 'jr2_kinova'
    if 'quad' in nm or mtype == 'aerial': return 'quadrotor'
    if mtype == 'legged' and _arm_specs(model)['has_arm']: return 'humanoid'
    if mtype == 'legged': return 'legged_robot'
    if mtype == 'wheeled' and _arm_specs(model)['has_arm']: return 'mobile_manipulator'
    if mtype == 'wheeled': return 'wheeled_base'
    return 'generic_robot'

# ---------- public API ----------

def parse_urdf_to_specs(urdf_path: str) -> Dict[str, Any]:
    """
    Parse URDF and extract standardized robot specifications.
    Only uses AVAILABLE data; unknowns are None.
    """
    with open(urdf_path, 'r') as f:
        xml = f.read()
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        # extremely malformed: minimal regex fallback
        return _regex_fallback(xml)

    root = _strip_ns(root)
    model = URDFModel(root)

    specs = {
        "robot_name": model.name,
        "robot_type": _robot_type_guess(model),
        "gripper": _gripper_specs(model),
        "arm": _arm_specs(model),
        "payload": _payload_specs(model),
        "base": _base_specs(model),
        "sensors": _sensor_specs(model),
    }
    return specs

def get_robot_summary(urdf_path: str) -> Dict[str, Any]:
    full = parse_urdf_to_specs(urdf_path)
    return {
        "type": full["robot_type"],
        "can_grasp": full["gripper"]["has_gripper"],
        "max_grasp_size": full["gripper"]["max_opening"],
        "max_reach": full["arm"]["max_reach"],
        "reach_height": full["arm"]["reach_height"],
        "mobility": full["base"]["mobility_type"],
        "has_vision": full["sensors"]["has_camera"],
    }

def _regex_fallback(xml: str) -> Dict[str,Any]:
    name = re.search(r'<robot\s+name="([^"]+)"', xml)
    robot_name = name.group(1) if name else "unknown_robot"
    rough = {
        "robot_name": robot_name,
        "robot_type": "generic_robot",
        "gripper": {"has_gripper": bool(re.search(r'(grip|finger|jaw)', xml, re.I)), "max_opening": None, "min_opening": None, "force_range": None},
        "arm": {"has_arm": bool(re.search(r'(shoulder|elbow|wrist|forearm|upperarm)', xml, re.I)), "degrees_of_freedom": None, "max_reach": None, "reach_height": None},
        "payload": {"max_weight": None, "max_torque": None},
        "base": {"footprint": None, "max_velocity": None, "mobility_type": ("aerial" if re.search(r'(rotor|propeller)', xml, re.I) else ("wheeled" if 'wheel' in xml.lower() else "fixed")), "has_mobility": None, "torso_lift": None},
        "sensors": {"has_camera": bool(re.search(r'(camera|rgbd|kinect|optical)', xml, re.I)), "has_depth": bool(re.search(r'(depth|rgbd|kinect)', xml, re.I)), "has_lidar": bool(re.search(r'(lidar|hokuyo|velodyne|laser|gpu_ray|<ray)', xml, re.I)), "camera_height": None, "camera_fov": None},
    }
    return rough