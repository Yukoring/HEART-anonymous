"""
HEART-extended DELTA prompts.

Extends two original DELTA prompt functions with heart_constraints injection:
- nl_prune_item → nl_prune_item_heart
- sg_2_pddl_problem → sg_2_pddl_problem_heart

All other prompt functions (nl_2_pddl_domain, decompose_problem, etc.)
are used directly from the original prompt.py without modification.
"""

from planners.delta.utils import utils


def nl_prune_item_heart(items_exp: dict, items_qry: dict, goal_exp: str, goal_qry: str,
                        item_keep_exp: list, domain_exp: str = None, domain_qry: str = None,
                        heart_constraints: str = ""):
    """
    Prune scene graph items — HEART-extended version.

    Same as original nl_prune_item, but injects HEART multi-agent analysis results
    to guide item pruning (e.g., exclude items marked infeasible by HEART agents).
    """
    act_exp, act_qry = None, None
    if domain_exp is not None:
        act_exp = "and the corresponding action knowledge\n{}".format(
            utils.get_pddl_domain_actions(domain_exp))
    if domain_qry is not None:
        act_qry = "and the new action knowledge\n{}".format(
            utils.get_pddl_domain_actions(domain_qry))

    content = "You are an excellent assistant in pruning items. Given a list of items and a goal description, you can prune the item list by only keeping the relevant items."

    heart_guidance = ""
    if heart_constraints:
        heart_guidance = f"""

    Multi-agent analysis results:
    {heart_constraints}

    Apply the Q/A constraints strictly: include only items explicitly allowed and feasible for the goal, and exclude any item marked impossible, disallowed, or inaccessible (per Multi-agent analysis).
    For example, if they indicate some item (object) is not pickable or there are some better objects, you should remove that object.
    """

    prompt = f"""
    Here is an example of a list of items: {items_exp}

    Given an example of a goal description: {goal_exp}, {act_exp}
    the relevant items for accomplishing the goal are {item_keep_exp}.

    Now given a new list of items: {items_qry}
    and a new goal description: {goal_qry}, {act_qry}
    {heart_guidance}
    Please provide a list of the relevent items from the new item list for accomplishing the new goal directly without further explanations, and keep the same data structure.
    """

    return content, prompt


def sg_2_pddl_problem_heart(domain_name_exp: str, domain_exp: str, problem_exp: str,
                            sg_exp: dict, sg_qry: dict, goal_exp: str, goal_qry: str,
                            domain_qry: str, domain_name_qry: str,
                            heart_constraints: str = ""):
    """
    Generate PDDL problem file — HEART-extended version.

    Same as original sg_2_pddl_problem, but appends HEART constraints as
    additional information to guide PDDL generation (objects, predicates,
    accessibility, affordances).
    """
    content = "You are an excellent PDDL problem file generator. Given a scene graph representation of an environment, a PDDL domain file and a goal description, you can generate a PDDL problem file."
    prompt = f"""
    Here is an example of a scene graph in the form of a nested dictionary in Python:
    ```\n{sg_exp}\n```\n
    The top level keys are the name of the scene, the rooms, the agents, and possibly the humans.
    Each room contains a dictionary of 'items' inside the rooms, and a list of 'neighbor' (connected) rooms. The 'neighbor' relation is bidirectional, i.e. if kitchen is neighbor of corridor, then corridor is also neighbor of kitchen.
    Each item has three attributes, 'accessible' means if the item can be accessed or not, 'affordance' indicates the affordable actions of this item, 'state' infers whether the item is free, or occupied, e.g. being picked by an agent.
    Each agent has two attributes, the current position and the state.

    Given a goal description e.g., {goal_exp}, and using the pre-defined object types, predicated in the PDDL domain example named {domain_name_exp}:
    ```\n{utils.get_pddl_domain_types(domain_exp)}\n{utils.get_pddl_domain_predicates(domain_exp)}\n```
    A corresponding PDDL problem file can be formulated as follows:
    ```\n{problem_exp}\n```
    The first line defines the name of the problem, usually the scene graph's name.
    The second line refers to the domain it based on.
    The "(:objects )" section lists all the items included in the scene graph with corresponding object types. Remember to distinguish the additional object types from the other items.
    The "(:init )" section lists the connections (neighbors) of the rooms in the scene graph, the positions of the items and the agent, and the attributes of all listed items (e.g. accessible, pickable, turnable etc.).
    The ; Connections part lists the neighbor rooms of all rooms in the scene graph. Note that the connection of each two neighbor rooms always exists as a pair, e.g. if there is a "(neighbor corridor kitchen)", there should always exist a "(neighbor kitchen corridor)".
    The ; Positions part lists the positions of all items and the agent in the scene graph.
    The ; Attributes part lists the attributes of all items in the scene graph.
    The "(:goal )" section defines the goal using the goal description given above.

    Now given a new scene graph: \n```\n{sg_qry}\n```
    and a new goal description: {goal_qry}
    and using the object types, predicates from the new PDDL domain file named {domain_name_qry}:
    ```\n{utils.get_pddl_domain_types(domain_qry)}\n{utils.get_pddl_domain_predicates(domain_qry)}\n```
    Please provide a new problem file in PDDL with respect to the new scene graph and goal specification directly without further explanations. Please also keep the comments such as "; Begin goal", "; End goal" etc. in the problem file.
    The goal should only consist of the previously defined predicates without any further keyword which not appear in the examples such as "forall" etc.

    Additional information: {heart_constraints}
    When generating the PDDL problem file, ensure all objects, predicates, and initial states from the constraints are faithfully included
    and consistently mapped to domain predicates, inferring any required enabling facts without inventing new elements.
    For attributes of items think about affordance and constraints.
    Also consider which items are accessible or not when you making the goals.
    """

    return content, prompt
