import sqlparse, re
from graphviz import Digraph
from flask import flash, render_template
#from .logic1 import check_syntax
 
# Define a class for creating nodes in a tree or graph structure
class Node:
    def __init__(self, value):
        self.key_ele = value  # Value associated with the node
        self.child = []       # List to store child nodes
   
    def visualize(self, graph, parent_node=None):
        """
        Recursively visualize the nodes and edges using graphviz.

        Parameters:
        - graph: A Digraph object from graphviz to add nodes and edges to.
        - parent_node: Name of the parent node in the visualization.
        """
        node_name = str(id(self))   # Unique identifier for the node
        node_label = str(self.key_ele)  # Label to display on the node
        
        # Add the node to the graph
        graph.node(node_name, label=node_label)
 
        # If there is a parent node, add an edge from parent to current node
        if parent_node:
            graph.edge(parent_node, node_name)
        
        # Recursively visualize child nodes
        for child in self.child:
            child.visualize(graph, node_name)

def aggregate(s):
    aggregates = ['MIN(', 'MAX(', 'SUM(', 'AVG(', 'COUNT(']
    for aggregate_func in aggregates:
        if s.startswith(aggregate_func):
            return True
    return False

is_cte_in_main = False

def sql_to_graph(parsed, root, ind, list_of_cte):
    global is_cte_in_main

    current_node = root
    parent_node = root
    tableNode_list = []
    is_aggregate = False

    while ind < len(parsed):
        clause = parsed[ind]

        if clause in {')', ')WITHEND', '),WITHEND', 'UNION', 'WITHUNION'}:
            break

        elif clause.upper() == 'SELECT':
            temp = Node('SELECT')
            j = ind + 1
            str_clause = 'SELECT\n\n( '
            aggregate_str = 'AGGREGATE \n\n'
            aggregate_dict = {}
            key_value = 1
            key_str = ''

            while parsed[j].upper() != 'FROM':
                if aggregate(parsed[j].upper()):
                    aggregate_str += parsed[j].upper()
                    key_str += parsed[j]
                    
                    while j < len(parsed) and parsed[j + 1].upper() != 'FROM' and parsed[j + 1][-1] != ',':
                        aggregate_str += ' ' + parsed[j + 1].upper()
                        key_str += ' ' + parsed[j + 1]
                        j += 1
                        
                    if parsed[j + 1][-1] == ',':
                        aggregate_str += ' ' + parsed[j + 1]
                        key_str += ' ' + parsed[j + 1]
                        j += 1
                    
                    str_clause += key_str + '\n'
                    aggregate_dict[key_value] = [key_str]
                    key_value += 1
                    key_str = ''
                    aggregate_str += '\n\n'
                    is_aggregate = True
                    
                elif parsed[j][-1] == ',':
                    str_clause += parsed[j] + '\n'
                    key_str += parsed[j]
                    aggregate_dict[key_value] = [key_str]
                    key_value += 1
                    key_str = ''
                    
                else:
                    str_clause += parsed[j] + ' '
                    key_str += parsed[j] + ' '
                    
                j += 1

            aggregate_dict[key_value] = [key_str]
            key_value += 1
            key_str = ''
            str_clause += ' )'
            temp.key_ele = str_clause
            parent_node = temp
            current_node = parent_node
            print(aggregate_dict)

        elif clause.upper() == 'FROM':
            if parsed[ind + 1] == '(':
                ind += 1
                continue
            else:
                tableNode = Node(parsed[ind + 1])
                j = ind + 1
                str_clause = 'FROM\n\n( '
                cte_table_name = ''

                while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() not in {'WHERE', 'JOIN', 'GROUP', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'LEFT', 'INNER', 'SELECT'}:
                    if parsed[j][-1] == ',':
                        str_clause += parsed[j]
                        cte_table_name += parsed[j][:-1]
                        tableNode.key_ele = 'SELF JOIN'
                        table = Node(cte_table_name)
                        tableNode.child.append(table)

                        for table_name in list_of_cte:
                            if cte_table_name == table_name.key_ele[6:]:
                                is_cte_in_main = True
                                table.child.append(table_name)
                                break

                        cte_table_name = ''
                        str_clause += '\n'

                    else:
                        cte_table_name += parsed[j]
                        str_clause += ' ' + parsed[j]

                    j += 1

                if tableNode.key_ele == 'SELF JOIN':
                    table = Node(cte_table_name)
                    tableNode.child.append(table)

                    for table_name in list_of_cte:
                        if cte_table_name == table_name.key_ele[6:]:
                            is_cte_in_main = True
                            table.child.append(table_name)
                            break

                if tableNode.key_ele != 'SELF JOIN':
                    str_clause += ' )'
                    tableNode.key_ele = str_clause

                    for table_name in list_of_cte:
                        if cte_table_name == table_name.key_ele[6:]:
                            is_cte_in_main = True
                            tableNode.child.append(table_name)
                            break

                tableNode_list.append(tableNode)

        elif clause.upper() == 'WHERE':
            j = ind + 1
            str_clause = 'WHERE\n\n( '

            while j < len(parsed) and parsed[j].upper() not in {'JOIN', 'GROUP', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                if parsed[j] == ')':
                    break

                if parsed[j] == '(':
                    str_clause += 'Subquery'
                    j += 1
                    count = 1

                    while count != 0:
                        if j < len(parsed) and count != 0 and parsed[j] == ')':
                            count -= 1
                        if j < len(parsed) and parsed[j] == '(':
                            count += 1
                        j += 1

                    j -= 1

                elif parsed[j].upper() in {'AND', 'OR'}:
                    str_clause += '\n' + parsed[j].upper() + ' '

                else:
                    str_clause += parsed[j] + ' '

                j += 1

            str_clause += ' )'
            temp = Node(str_clause)
            current_node.child.append(temp)

        elif clause.upper() == 'JOIN':
            str_clause = ''

            if parsed[ind - 1].upper() in {'LEFT', 'RIGHT', 'INNER', 'FULL', 'CROSS', 'SELF', 'OUTER'}:
                str_clause += parsed[ind - 1].upper() + ' JOIN\n\n( '

            j = ind + 1
            second_table = 'FROM\n\n( '
            cte_table_name = ''
            list_of_cte_table = []

            while parsed[j].upper() != 'ON':
                if parsed[j][-1] == ',':
                    second_table += parsed[j]
                    cte_table_name += parsed[j][:-1]

                    for table_name in list_of_cte:
                        if table_name.key_ele[6:] == cte_table_name:
                            is_cte_in_main = True
                            list_of_cte_table.append(table_name)
                            break

                    cte_table_name = ''

                else:
                    second_table += ' ' + parsed[j]
                    cte_table_name += parsed[j]

                j += 1

            for table_name in list_of_cte:
                if table_name.key_ele[6:] == cte_table_name:
                    is_cte_in_main = True
                    list_of_cte_table.append(table_name)
                    break

            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() not in {'WHERE', 'GROUP', 'JOIN', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                if parsed[j][-1] == ',' or parsed[j].upper() in {'AND', 'OR'}:
                    str_clause += parsed[j] + '\n'

                else:
                    str_clause += parsed[j] + ' '

                j += 1

            str_clause += ' )'
            temp = Node(str_clause)
            temp.child.append(parent_node)
            parent_node = temp

            second_table += ' )'
            temp = Node(second_table)

            for table_name in list_of_cte_table:
                temp.child.append(table_name)

            tableNode_list.append(temp)

        elif clause.upper() == 'GROUP':
            j = ind + 2
            str_clause = 'GROUP BY\n\n( '

            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() not in {'HAVING', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                pattern = r'^-?\d+$'
                if parsed[j][-1] == ',':
                    string_result = bool(re.match(pattern, parsed[j][:-1]))
                    if string_result:
                        str_clause += aggregate_dict[int(parsed[j][:-1])][0] + '\n'
                    else:
                        str_clause += parsed[j] + '\n'

                else:
                    string_result = bool(re.match(pattern, parsed[j]))
                    if string_result:
                        str_clause += aggregate_dict[int(parsed[j])][0] + ' '
                    else:
                        str_clause += parsed[j] + ' '

                j += 1

            str_clause += ' )'
            temp = Node(str_clause)
            temp.child.append(parent_node)
            parent_node = temp

        elif clause.upper() == 'HAVING':
            j = ind + 1
            str_clause = 'HAVING\n\n( '

            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() not in {'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                if parsed[j][-1] == ',':
                    str_clause += parsed[j] + '\n'

                else:
                    str_clause += parsed[j] + ' '

                j += 1

            str_clause += ' )'
            temp = Node(str_clause)
            temp.child.append(parent_node)
            parent_node = temp

        elif clause.upper() == 'ORDER':
            j = ind + 2
            str_clause = 'ORDER BY\n\n( '

            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() not in {'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                if parsed[j][-1] == ',':
                    str_clause += parsed[j] + '\n'

                else:
                    str_clause += parsed[j] + ' '

                j += 1

            str_clause += ' )'
            temp = Node(str_clause)
            temp.child.append(parent_node)
            parent_node = temp

        elif clause.upper() == 'LIMIT' and parsed[j].upper() not in {'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
            j = ind + 1
            str_clause = 'LIMIT\n\n( '

            while j < len(parsed) and parsed[j] != ')':
                if parsed[j][-1] == ',':
                    str_clause += parsed[j] + '\n'

                else:
                    str_clause += parsed[j] + ' '

                j += 1

            str_clause += ' )'
            temp = Node(str_clause)
            temp.child.append(parent_node)
            parent_node = temp

        elif clause == '(' and parsed[ind + 1].upper() == 'SELECT':
            root_subquery = Node('null')
            root_subquery = sql_to_graph(parsed, root_subquery, ind + 1, list_of_cte)

            if is_aggregate:
                temp = Node(aggregate_str)
                temp.child.append(root_subquery)
                root_subquery = temp

            tmp = Node('Subquery')

            if parsed[ind - 1].upper() in {'FROM', 'WHERE', 'AND', 'OR', '=', '>', '<', 'IN', 'LIKE', 'AS', '!='}:
                for node in current_node.child:
                    if 'Subquery' in node.key_ele.lower():
                        tmp.child.append(root_subquery)
                        node.child.append(tmp)
                        break

            elif parsed[ind - 1].upper() == 'JOIN':
                tmp.child.append(root_subquery)
                parent_node.child.append(tmp)

            else:
                current_node.child.append(root_subquery)

            count = 1
            ind += 1

            while count != 0:
                if ind < len(parsed) and count != 0 and parsed[ind] == ')':
                    count -= 1

                if ind < len(parsed) and parsed[ind] == '(':
                    count += 1

                ind += 1

            ind -= 1

        ind += 1

    if len(current_node.child) >= 1:
        for node in current_node.child:
            for table_Node in tableNode_list:
                node.child.append(table_Node)
    else:
        for table_Node in tableNode_list:
            current_node.child.append(table_Node)

    if is_aggregate:
        temp = Node(aggregate_str)
        temp.child.append(parent_node)
        parent_node = temp

    return parent_node


def print_graph(root):
    """
    Prints the tree structure of the SQL parse tree.

    Parameters:
    root (Node): The root node of the tree.
    """
    if len(root.child) == 0:
        return
    queue = []
    queue.append(root)
    while len(queue) > 0:
        node = queue.pop(0)

        # Print the node and its children
        print(node.key_ele + ':  [', end="")
        i = 1
        for ele in node.child:
            if i < len(node.child):
                print(ele.key_ele + '; ', end="")
            else:
                print(ele.key_ele + ']', end="")
            i += 1
            queue.append(ele)
        if len(node.child) == 0:
            print(']')

def main2(query):
    global is_cte_in_main
    """
    Main function to process the SQL query and visualize its parse tree.

    Parameters:
    query (str): The SQL query to be processed.

    Returns:
    str: Path to the generated visualization image.
    """
    # Replace newline characters and adjust spacing around commas
    query = query.replace('\n', ' ')
    query = query.replace(', ', ',')
    query = query.replace(',', ', ')

    try:
        # Split the query into tokens
        parsed = query.split()
        list_of_cte = []
        i = 0

        # Process Common Table Expressions (CTEs)
        while i < len(parsed):
            if parsed[i].upper() == 'WITH':
                str = 'CTE -'
                i += 1
                # Accumulate the CTE name
                while i < len(parsed) and parsed[i].upper() != 'AS':
                    str += ' ' + parsed[i]
                    i += 1
                tmp = Node(str)
                list_of_cte.append(tmp)
                # Mark the end of CTE
                while i < len(parsed) and parsed[i] != ')' and parsed[i] != '),':
                    if parsed[i].upper() == 'SELECT':
                        parsed[i] = 'WITHSELECT'
                    if parsed[i].upper() == 'UNION':
                        parsed[i] = 'WITHUNION'
                    i += 1
                if parsed[i] == ')' or parsed[i] == '),':
                    if parsed[i] == '),':
                        parsed.insert(i + 1, 'WITH')
                    parsed[i] += 'WITHEND'
            i += 1

        # Initialize graph and tree structure variables
        graph = Digraph()
        list_of_main_root = []
        root = Node('Null')
        i = 0
        ind_of_cte = 0
        cteroot = Node('CTE')
        is_main_root = False
        is_create_node = False
        is_cte = False
        # Parse the tokens and build the tree structure
        while i < len(parsed):
            if parsed[i].upper() == 'CREATE':
                is_create_node = True
                CreateNode = Node(parsed[i].upper())
                i += 1
                # Accumulate CREATE TABLE statement
                while parsed[i].upper() != 'TABLE':
                    CreateNode.key_ele += ' ' + parsed[i].upper()
                    i += 1
                CreateNode.key_ele += ' ' + parsed[i].upper() + '\n'
                i += 1
                while parsed[i].upper() != 'AS':
                    if parsed[i][-1] == ',':
                        CreateNode.key_ele += parsed[i] + '\n'
                    else:
                        CreateNode.key_ele += parsed[i] + ' '
                    i += 1

            # Process SELECT statements
            if parsed[i].upper() == 'SELECT':
                if i == 0 or (i != 0 and parsed[i - 1] != '('):
                    root = Node('Null')
                    root = sql_to_graph(parsed, root, i, list_of_cte)
                    print_graph(root)
                    is_main_root = True
                    list_of_main_root.append(root)

            # Process UNION statements
            elif parsed[i].upper() == 'UNION':
                tmp = Node('UNION ALL')
                if parsed[i + 1].upper() != 'ALL':
                    tmp.key_ele = 'UNION'
                tmp.child.append(root)
                root = tmp
                root1 = Node('Null')
                if parsed[i + 1].upper() != 'ALL':
                    root1 = sql_to_graph(parsed, root1, i + 1, list_of_cte)
                    i += 1
                else:
                    root1 = sql_to_graph(parsed, root1, i + 2, list_of_cte)
                    i += 2
                root.child.append(root1)

            # Handle CTE specific SELECT and UNION
            elif parsed[i] == 'WITHSELECT':
                root = Node('Null')
                parsed[i] = 'SELECT'
                root = sql_to_graph(parsed, root, i, list_of_cte)
                is_cte = True
            elif parsed[i] == 'WITHUNION':
                parsed[i] = 'UNION'
                tmp = Node('UNION ALL')
                if parsed[i + 1].upper() != 'ALL':
                    tmp.key_ele = 'UNION'
                tmp.child.append(root)
                root = tmp
                root1 = Node('Null')
                if parsed[i + 1].upper() != 'ALL':
                    parsed[i + 1] = 'SELECT'
                    root1 = sql_to_graph(parsed, root1, i + 1, list_of_cte)
                    i += 1
                else:
                    parsed[i + 2] = 'SELECT'
                    root1 = sql_to_graph(parsed, root1, i + 2, list_of_cte)
                    i += 2
                root.child.append(root1)

            # Attach CTEs to the main root
            elif parsed[i] == ')WITHEND' or parsed[i] == '),WITHEND':
                list_of_cte[ind_of_cte].child.append(root)
                root = list_of_cte[ind_of_cte]
                cteroot.child.append(root)
                ind_of_cte += 1

            i += 1

        # Determine the final root node
        if not is_main_root:
            root = cteroot
        if is_create_node:
            CreateNode.child.append(root)
            root = CreateNode
        if is_cte_in_main == False and is_cte == True:
            cteroot.visualize(graph)

        # Print and visualize the final parse tree
        print_graph(root)
        root.visualize(graph)
        graph.render('node_structure2', format='png', cleanup=True)
        return 'node_structure2.png'
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == '__main__':
    query = "Select job_id, salary from job group by 1, 2"
    main2(query)