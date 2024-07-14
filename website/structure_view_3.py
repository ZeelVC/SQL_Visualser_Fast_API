import sqlparse
from graphviz import Digraph
from flask import Flask, request, render_template, flash

app = Flask(__name__)
app.secret_key = 'supersecretkey'

class Node:
    """
    Class to represent a node in the SQL parse tree.
    
    Attributes:
    key_ele (str): The value of the node.
    child (list): List of child nodes.
    """
    def __init__(self, value):
        self.key_ele = value
        self.child = []

    def visualize(self, graph, parent_node=None):
        """
        Visualizes the tree structure using Graphviz.

        Parameters:
        graph (Digraph): The Graphviz Digraph object.
        parent_node (str): The parent node in the graph.
        """
        # Generate a unique node name
        node_name = str(id(self))
        node_label = str(self.key_ele)
        graph.node(node_name, label=node_label)

        # Draw edge between parent node and current node
        if parent_node:
            graph.edge(parent_node, node_name)
        
        # Recursively visualize child nodes
        for child in self.child:
            child.visualize(graph, node_name)

def aggregate(str):
    """
    Checks if a given string is an aggregate function.

    Parameters:
    str (str): The string to check.

    Returns:
    bool: True if the string is an aggregate function, False otherwise.
    """
    # Define list of aggregate functions
    aggregates = ['MIN(', 'MAX(', 'SUM(', 'AVG(', 'COUNT(']

    # Check if the string starts with any aggregate function
    return any(str.upper().startswith(agg) for agg in aggregates)

is_cte_in_main = False

def sql_to_graph(parsed, root, ind, list_of_cte):
    global is_cte_in_main
    """
    Converts parsed SQL query tokens into a tree structure.

    Parameters:
    parsed (list): List of parsed SQL tokens.
    root (Node): The root node of the tree.
    ind (int): Current index in the parsed tokens.
    list_of_cte (list): List of Common Table Expressions (CTEs).

    Returns:
    Node: The root node of the generated tree.
    """
    current_node = root
    parent_node = root
    tableNode = Node('Null')

    while ind < len(parsed):
        clause = parsed[ind]

        # Handle end of clause scenarios
        if clause in [')', ')WITHEND', '),WITHEND', 'UNION', 'WITHUNION']:
            break
        elif clause.upper() == 'SELECT':
            tmp = Node('SELECT')
            j = ind + 1
            isaggr = False

            # Determine if there is an aggregate function in the SELECT clause
            while parsed[j].upper() != 'FROM':
                if aggregate(parsed[j].upper()):
                    isaggr = True
                    break
                j += 1
        elif clause.upper() == 'FROM':
            if parsed[ind + 1] == '(':
                ind += 1
                continue
            else:
                # Handle table names in FROM clause
                tableNode = Node(parsed[ind + 1])
                j = ind + 1
                str = '' 
                cte_table_name = ''

                # Process tables in the FROM clause
                while j < len(parsed) and parsed[j] not in [')', 'WHERE', 'JOIN', 'GROUP', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'LEFT', 'INNER']:
                    if parsed[j][-1] == ',':
                        str += parsed[j]
                        cte_table_name += parsed[j][:-1]
                        tableNode.key_ele = 'SELF JOIN'
                        table = Node(cte_table_name)
                        tableNode.child.append(table)
                        
                        # Check if table is a CTE
                        for table_name in list_of_cte:
                            if cte_table_name == table_name.key_ele[6:]:
                                is_cte_in_main = True
                                table.child.append(table_name)
                                break
                        cte_table_name = ''
                        str += '\n'
                    else:
                        cte_table_name += parsed[j]
                        str += ' ' + parsed[j]
                    j += 1
                
                # Finalize table node for CTEs
                if tableNode.key_ele == 'SELF JOIN':
                    table = Node(cte_table_name)
                    tableNode.child.append(table)
                    for table_name in list_of_cte:
                        if cte_table_name == table_name.key_ele[6:]:
                            is_cte_in_main = True
                            tableNode.child.append(table_name)
                            break
                if tableNode.key_ele != 'SELF JOIN':        
                    tableNode.key_ele = str
                    for table_name in list_of_cte:
                        if cte_table_name == table_name.key_ele[6:]:
                            is_cte_in_main = True
                            tableNode.child.append(table_name)
                            break
        elif clause.upper() == 'WHERE':
            if parsed[ind + 1] == '(':
                ind += 1
                continue
        elif clause.upper() == 'JOIN':
            # Handle JOIN clause
            str = ''
            if parsed[ind-1].upper() in ['LEFT', 'RIGHT', 'INNER', 'FULL', 'CROSS', 'SELF', 'OUTER']:
                str += parsed[ind-1].upper() + ' '
            str += 'JOIN'
            j = ind + 1
            second_table = ''
            cte_table_name = ''
            list_of_cte_table = []

            # Process tables in the JOIN clause
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

            # Finalize CTE tables in the JOIN clause
            for table_name in list_of_cte:
                if table_name.key_ele[6:] == cte_table_name:
                    is_cte_in_main = True
                    list_of_cte_table.append(table_name)
                    break

            if parent_node.key_ele == 'Null':
                temp = Node(str)
                parent_node = temp
                current_node = temp
            else:
                temp = Node(str)
                temp.child.append(parent_node)
                parent_node = temp

            if parsed[ind + 1] != '(':
                temp = Node(second_table)
                parent_node.child.append(temp)
                for table_name in list_of_cte_table:
                    temp.child.append(table_name)
        elif clause.upper() == 'GROUP':
            pass
        elif clause.upper() == 'HAVING':
            pass
        elif clause.upper() == 'ORDER':
            pass
        elif clause.upper() == 'LIMIT':
            pass
        elif clause == '(' and parsed[ind + 1].upper() == 'SELECT':
            root_subquery = Node('Null')
            root_subquery = sql_to_graph(parsed, root_subquery, ind + 1, list_of_cte)
            tmp = Node('Subquery')

            # Handle subqueries
            if parsed[ind - 1].upper() in ['FROM', 'WHERE', 'AND', 'OR', '=', '>', '<', 'IN', 'LIKE', 'AS', '!=']:
                tableNode.child.append(tmp)
                tmp.child.append(root_subquery)
                if tableNode.key_ele == 'Null':
                    tableNode = tableNode.child[0]
            elif parsed[ind - 1].upper() == 'JOIN':
                parent_node.child.append(tmp)
                tmp.child.append(root_subquery)
            else:
                current_node.child.append(root_subquery)
            count = 1
            ind += 1
            while count != 0:
                if ind < len(parsed) and parsed[ind] == ')':
                    count -= 1
                if ind < len(parsed) and parsed[ind] == '(':
                    count += 1
                ind += 1
            ind -= 1
        ind += 1

    # Set the final parent node
    if current_node.key_ele == 'Null':
        parent_node = tableNode
    else:
        current_node.child.append(tableNode)
    
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

def check_syntax(query, ind):
    """
    Checks the syntax of the SQL query.

    Parameters:
    query (str): The SQL query to check.
    ind (int): The starting index for checking.

    Returns:
    bool: True if the syntax is invalid, False otherwise.
    """
    # Check for initial SELECT clause
    if query[ind:ind + 6].upper() != 'SELECT':
        return True
    while ind < len(query):
        if query[ind:ind + 6].upper() == 'SELECT':
            if ind + 6 > len(query):
                return True
            ind += 6
            while query[ind] == ' ':
                ind += 1
            if query[ind] == ',':
                return True
        elif query[ind:ind + 4].upper() == 'FROM':
            if ind + 4 > len(query) or query[ind + 4] != ' ':
                return True
            if query[ind + 4:ind + 9].upper() in ['WHER', 'JOIN', 'ORDE', 'GROU', 'HAVI', 'LIMI']:
                return True
            j = ind + 4
            while query[j:j + 5].upper() != 'WHERE' and query[j:j + 5].upper() != 'GROUP' and query[j:j + 5].upper() != 'ORDER' and query[j:j + 4].upper() != 'JOIN':
                if query[j:j + 2].upper() in ['IN', 'LI', 'EX', 'IS']:
                    return True
                j += 1
        ind += 1
    return False

def main1(query):
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
        graph.render('node_structure1', format='png', cleanup=True)
        return 'node_structure1.png'
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == '__main__':
    query = "Select job_id, salary from job group by 1, 2"
    main1(query)
