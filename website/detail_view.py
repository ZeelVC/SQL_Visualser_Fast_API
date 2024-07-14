import sqlparse
import re
from graphviz import Digraph
from flask import flash, render_template

# Creating Tree Data Structures to store the ouput of SQL visualization.
# Haivng a node and list of its child nodes.

class Node:
    def __init__(self, value):
        self.key_ele = value
        self.child = []
   
    def visualize(self, graph, parent_node=None):
        node_name = str(id(self))
        node_label = str(self.key_ele)
        graph.node(node_name, label=node_label)
 
        if parent_node:
            graph.edge(parent_node, node_name)
        for child in self.child:
            child.visualize(graph, node_name)
 
# aggregate function check the input string whether it is a aggregate function.

def aggregate(func_str):
    aggregates = ['MIN', 'MAX', 'SUM', 'AVG', 'COUNT']
    return any(func_str.startswith(agg + '(') for agg in aggregates)

# the below variable is created to check wheter the CTE table are used in main query.

is_cte_in_main = False


# The sql_to graph function is main function of overall logic
# required to convert parsed SQL into graphical form.


def sql_to_graph(parsed, root, ind, list_of_cte, dict_of_cte_table):
    global is_cte_in_main
    current_node = root
    parent_node = root
    tableNode = Node('0')
    tableNode_list = []
    isaggr = False

    # For building the logic part, iterating to the parsed SQL
    # Based on the clauses of SQL, logic part for each of these clause are written

    while ind < len(parsed):
        clause = parsed[ind]
        #close bracket code, indication there was a subquery
        if clause in {')', ')WITHEND', '),WITHEND', 'UNION', 'WITHUNION'}:
            break

        # select clause condition
        # iterating the list of SQL or parsed SQL, whenever encounter the 'select' clause
        # make it the current node and parent node as it is the first node of the graphical form.
        # This also checks the presence of agrregate funciton in SQL.
        # Output: - A node having value 'Select <line break> ...couple of columns...'

        elif clause.upper() == 'SELECT':
            temp = Node('SELECT')
            j = ind + 1
            str = 'SELECT\n\n( '
            aggr = 'AGGREGATE \n\n'
            dict = {}
            key_value = 1
            key_str = ''
            while parsed[j].upper() != 'FROM':
                if aggregate(parsed[j].upper()):
                    aggr+=parsed[j].upper()
                    key_str += parsed[j]
                    while j < len(parsed) and parsed[j + 1].upper() != 'FROM' and parsed[j + 1][len(parsed[j + 1]) - 1] != ',':
                        aggr += ' ' + parsed[j + 1].upper()
                        key_str += ' ' + parsed[j + 1]
                        j+=1
                    if parsed[j + 1][len(parsed[j + 1]) - 1] == ',':
                        aggr += ' ' + parsed[j + 1] 
                        key_str += ' ' + parsed[j + 1]
                        j += 1
                    dict[key_value] = []
                    dict[key_value].append(key_str)
                    key_value+=1
                    str += key_str + '\n'
                    key_str = ''
                    aggr +='\n\n'
                    isaggr = True
                elif parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
                    key_str += parsed[j]
                    dict[key_value] = []
                    dict[key_value].append(key_str)
                    key_value+=1
                    key_str = ''
                else:
                    str += parsed[j] + ' '
                    key_str+=parsed[j] + ' '
                j +=1
            ind = j - 1
            dict[key_value] = []
            dict[key_value].append(key_str)
            key_value+=1
            key_str = ''
            str += ' )'
            temp.key_ele = str  
            parent_node = temp
            current_node = parent_node
            print(dict)

        # From clause condition
        # Iterating to the parsed SQL, whenevr encounter the 'from' clause
        # appending table node into tableNodeList and parent node and current node is still the same.
        # This also checks the presence of CTE table, and if present
        # It will add CTE table into its child.
        # Also checking whether the from clause have multiple table,
        # as multiple table represents the SELF JOIN between them
        # This also checks whether it uses the table, that has been created
        # in the previous queries.
        elif clause.upper() == 'FROM':
            if parsed[ind + 1] == '(':
                ind+=1
                continue
            else:
                tableNode = Node(parsed[ind + 1])
                j = ind + 1
                str = 'FROM\n\n( ' 
                cte_table_name = ''
                while j < len(parsed) and parsed[j].upper() not in {')', 'WHERE', 'JOIN', 'GROUP', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'LEFT', 'INNER', 'SELECT'}:

                    # Checking for multiple table being used or not.
                    if parsed[j][len(parsed[j]) - 1] == ',':
                        str += parsed[j]
                        cte_table_name += parsed[j][0 : len(parsed[j]) - 1]
                        tableNode.key_ele = 'SELF JOIN'
                        table = Node(cte_table_name)
                        tableNode.child.append(table)

                        # Checking if CTE table are used.
                        for table_name in list_of_cte:
                            if cte_table_name[0:len(table_name.key_ele) - 6] == table_name.key_ele[6:]:
                                is_cte_in_main = True
                                table.child.append(table_name)
                                break
                        k = 0
                        string = ""
                        while k < len(cte_table_name):
                            if cte_table_name[k:k+2].upper() == 'AS' and cte_table_name[k-1].upper() not in {'B'}:
                                break
                            else:
                                string += cte_table_name[k]
                            k+=1

                        # Checking if table that is created in previous queries is used.
                        if len(dict_of_cte_table) > 1:
                            if dict_of_cte_table.get(string) != None:
                                num = dict_of_cte_table[string]
                                table.key_ele += '\n' + '(Table Created in Query ' + f'{num}' + ')'
                        cte_table_name = ''
                        str += '\n'
                    else:
                        cte_table_name+=parsed[j]
                        str += ' ' + parsed[j]
                    j+=1

                # Handling the final table if multiple table has been used.
                if tableNode.key_ele == 'SELF JOIN':
                    table = Node(cte_table_name)
                    tableNode.child.append(table)

                    # Checking if CTE table are used.
                    for table_name in list_of_cte:
                        if cte_table_name[0:len(table_name.key_ele) - 6] == table_name.key_ele[6:]:
                            is_cte_in_main = True
                            table.child.append(table_name)
                            break
                    k = 0
                    string = ""
                    while k < len(cte_table_name):
                        if cte_table_name[k:k+2].upper() == 'AS' and cte_table_name[k-1].upper() not in {'B'}:
                            break
                        else:
                            string += cte_table_name[k]
                        k+=1

                    # Checking if table that is created in previous queries is used.
                    if len(dict_of_cte_table) > 1:
                        if dict_of_cte_table.get(string) != None:
                            num = dict_of_cte_table[string]
                            table.key_ele += '\n' + '(Table Created in Query ' + f'{num}' + ')'

                # Hanlding the case if multiple table are not there.
                if tableNode.key_ele != 'SELF JOIN':  
                    str+= ' )'      
                    tableNode.key_ele = str

                    # Checking if CTE table are used.
                    for table_name in list_of_cte:
                        if cte_table_name[0:len(table_name.key_ele) - 6] == table_name.key_ele[6:]:
                            is_cte_in_main = True
                            tableNode.child.append(table_name)
                            break
                    k = 0
                    string = ""
                    while k < len(cte_table_name):
                        if cte_table_name[k:k+2].upper() == 'AS' and cte_table_name[k-1].upper() not in {'B'}:
                            break
                        else:
                            string += cte_table_name[k]
                        k+=1

                    # Checking if table that is created in previous queries is used.
                    if len(dict_of_cte_table) > 1:
                        if dict_of_cte_table.get(string) != None:
                            num = dict_of_cte_table[string]
                            tableNode.key_ele += '\n' + '(Table Created in Query ' + f'{num}' + ')'
                tableNode_list.append(tableNode)
 
        # Where clause condition
        # Iterating the parsed SQL, whenever encounter 'where' clause
        # Making it the current node and child of parent node, parent node stills remain the same.
        elif clause.upper() == 'WHERE':
            j = ind + 1
            str = 'WHERE\n\n( '
            while j < len(parsed) and parsed[j].upper() not in {')', 'JOIN', 'GROUP', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                #if parsed[j] == ')':
                #   break
                if parsed[j] == '(':
                    str+='Subquery' 
                    j+=1
                    count = 1
                    while count != 0:
                        if j < len(parsed) and count != 0 and parsed[j] == ')':
                            count-=1
                        if j < len(parsed) and parsed[j] == '(':
                            count+=1
                        j+=1
                    j-=1
                elif parsed[j].upper() == 'AND' or parsed[j].upper() == 'OR':
                    str += '\n'+parsed[j].upper()+' '
                #    temp = Node(str)
                #    current_node.child.append(temp)
                #    str = 'WHERE' + '\n\n( '
                else:
                    #if parsed[j][len(parsed[j]) - 1] == ',':
                    #    str += parsed[j] + '\n'
                    #else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            current_node.child.append(temp)


        # Join clause condition
        # Iterating the parsed SQl, whenever encounter the 'JOIN' clause
        # making it the parent node, the previous parent node as its child.
        # current node remains the same.
        # Basically iterating till ON clause, and store the table node
        # This table node will become its child.
        # This also checks the presence of CTE table, and if present
        # it will add CTE table into its child.
        # and then whatever condition is used for joining will be stored like:
        # JOIN <line break> ON ( Condition )
        # This also checks whether it uses the table, that has been created
        # in the previous queries.
        elif clause.upper() == 'JOIN':
            join_type = parsed[ind-1].upper() if parsed[ind-1].upper() in {'LEFT', 'RIGHT', 'INNER', 'FULL', 'CROSS', 'SELF', 'OUTER'} else ''
            str = f'{join_type} JOIN\n\n( '
            j = ind + 1
            second_table = 'FROM\n\n( '
            cte_table_name = ''
            list_of_cte_table = []

            # Storing table name
            while parsed[j].upper() != 'ON':

                # Handling id multiple table are there
                if parsed[j][len(parsed[j]) - 1] == ',':
                    second_table += parsed[j]
                    cte_table_name += parsed[j][0 : len(parsed) - 1]

                    # Checking if CTE table are used.
                    for table_name in list_of_cte:
                        if table_name.key_ele[6:] == cte_table_name[0:len(table_name.key_ele) - 6]:
                            is_cte_in_main = True
                            list_of_cte_table.append(table_name)
                            break
                    k = 0
                    string = ""
                    while k < len(cte_table_name):
                        if cte_table_name[k:k+2].upper() == 'AS' and cte_table_name[k-1].upper() not in {'B'}:
                            break
                        else:
                            string += cte_table_name[k]
                        k+=1

                    # Checking if table that is created in previous queries is used.
                    if len(dict_of_cte_table) > 1:
                        if dict_of_cte_table.get(string) != None:
                            second_table += '\n' + '(Table Created in Query ' + f'{dict_of_cte_table[string]}' + ')\n'
                    cte_table_name = ''
                elif parsed[j] == '(':
                    second_table += 'Subquery'
                    j+=1
                    count = 1
                    while count != 0:
                        if j < len(parsed) and count != 0 and parsed[j] == ')':
                            count-=1
                        if j < len(parsed) and parsed[j] == '(':
                            count+=1
                        j+=1
                    j-=1
                else:
                    second_table += ' ' + parsed[j]
                    cte_table_name += parsed[j]
                j+=1

            # Handling if multiple table are not there.
            # Checking if CTE table are used.
            for table_name in list_of_cte:
                if table_name.key_ele[6:] == cte_table_name[0:len(table_name.key_ele) - 6]:
                    is_cte_in_main = True
                    list_of_cte_table.append(table_name)
                    break
            k = 0
            string = ""
            while k < len(cte_table_name):
                if cte_table_name[k:k+2].upper() == 'AS' and cte_table_name[k-1].upper() not in {'B'}:
                    break
                else:
                    string += cte_table_name[k]
                k+=1

            # Checking if table that is created in previous queries is used.
            if len(dict_of_cte_table) > 1:
                if dict_of_cte_table.get(string) != None:
                    second_table += '\n' + '(Table Created in Query ' + f'{dict_of_cte_table[string]}'+')'
            while j < len(parsed) and parsed[j].upper() not in {')', 'WHERE', 'GROUP', 'JOIN', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                if parsed[j][len(parsed[j]) - 1] == ',' or parsed[j].upper() == 'AND' or parsed[j].upper() == 'OR':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp    
            #if parsed[ind + 1] != '(':
            #    temp = Node(second_table)
            #    parent_node.child.append(temp)
            #    for table_name in list_of_cte_table:
            #        temp.child.append(table_name)
            second_table += ' )'
            temp = Node(second_table)
            for table_name in list_of_cte_table:
                temp.child.append(table_name)
            tableNode_list.append(temp)
 
        # group by clause condition
        # Iterating to the parsed SQL, whenever encounter 'group by' clause 
        # making it the parent node and the previous parent node as its child
        # current node remains the same.
        elif clause.upper() == 'GROUP':
            j = ind + 2
            str = 'GROUP BY\n\n( '
            while j < len(parsed) and parsed[j].upper() not in {')', 'HAVING', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                pattern = r'^-?\d+$'
                if parsed[j][len(parsed[j]) - 1] == ',':
                    string_result = bool(re.match(pattern, parsed[j][:-1]))
                    if string_result: 
                        str += dict[int(parsed[j][0:len(parsed[j]) - 1])][0] + '\n'
                    else:
                        str += parsed[j] + '\n'
                else:
                    string_result = bool(re.match(pattern, parsed[j][-1]))
                    if string_result: 
                        str += dict[int(parsed[j])][0] + ' '
                    else:
                        str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
 
        # Having clause condition
        # Iterating to the parsed SQL, whenever encounter 'group by' clause 
        # making it the parent node and the previous parent node as its child
        # current node remains the same.
        elif clause.upper() == 'HAVING':
            j = ind + 1
            str = 'HAVING' + '\n\n( '
            while j < len(parsed) and parsed[j].upper() not in {')', 'ORDER', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                if parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
       
        # Order by clause condition
        # Iterating to the parsed SQL, whenever encounter 'group by' clause 
        # making it the parent node and the previous parent node as its child
        # current node remains the same.
        elif clause.upper() == 'ORDER':
            j = ind + 2
            str = 'ORDER BY\n\n( '
            while j < len(parsed) and parsed[j].upper() not in {')', 'LIMIT', 'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
                pattern = r'^-?\d+$'
                if parsed[j][len(parsed[j]) - 1] == ',':
                    string_result = bool(re.match(pattern, parsed[j][:-1]))
                    if string_result: 
                        str += dict[int(parsed[j][0:len(parsed[j]) - 1])][0] + '\n'
                    else:
                        str += parsed[j] + '\n'
                else:
                    string_result = bool(re.match(pattern, parsed[j][-1]))
                    if string_result: 
                        str += dict[int(parsed[j])][0] + ' '
                    else:
                        str += parsed[j] + ' '
                j += 1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
 
        # Limit clause condition
        # Iterating to the parsed SQL, whenever encounter 'group by' clause 
        # making it the parent node and the previous parent node as its child
        # current node remains the same.
        elif clause.upper() == 'LIMIT' and parsed[j].upper() not in {'UNION', 'WITHUNION', ')WITHEND', '),WITHEND', 'SELECT'}:
            j = ind + 1
            str = 'LIMIT' + '\n\n( '
            while j < len(parsed) and parsed[j] != ')':
                if parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
 
        # subquery conditon
        # Creating Subquery node and calling the same function.
        # On the basis of subquery is starting after which clause,
        # adding Subquery node accordingly: - 
        # In case of join, add the subquery to the child of parent node
        # while in rest cases to the child of current node

        elif clause == '(' and parsed[ind + 1].upper() == 'SELECT':
            root_subquery = Node('null')
            #j = ind + 2
            #str = 'SELECT' + '\n\n( '
            #aggr = 'AGGREGATE \n\n'
            #isaggr = False
            #while parsed[j].upper() != 'FROM':
            #    if aggregate(parsed[j].upper()):
            #        aggr+= ' ' + parsed[j].upper()
            #        isaggr = True
            #    elif parsed[j][len(parsed[j]) - 1] == ',':
            #        str += parsed[j] + '\n'
            #    else:
            #        str += parsed[j] + ' '
            #    j+=1
            #str += ' )'
            #root_subquery.key_ele = str
            root_subquery = sql_to_graph(parsed, root_subquery, ind + 1, list_of_cte, dict_of_cte_table)
            if isaggr:
                temp = Node(aggr)
                temp.child.append(root_subquery)
                root_subquery = temp
            tmp = Node('Subquery')
            if parsed[ind - 1].upper() == 'FROM':
                tableNode.child.append(tmp)
                tmp.child.append(root_subquery)
                tableNode = tmp
                tableNode_list.append(tableNode)
            elif parsed[ind - 1].upper() in {'WHERE', 'AND', 'OR', '=', '>', '<', 'IN', 'LIKE', 'AS', '!=', 'EXISTS'}:
                for node in current_node.child:
                    if node.key_ele.find('Subquery') != -1:
                        tmp.child.append(root_subquery)
                        node.child.append(tmp)
                        break
            elif parsed[ind - 1].upper() == 'JOIN':
                tmp.child.append(root_subquery)
                for table_Node in tableNode_list:
                    if table_Node.key_ele.find('Subquery') != -1:
                        table_Node.child.append(tmp)
                        break
            else:
                current_node.child.append(root_subquery)
            count = 1
            ind += 1
            while count != 0:
                if ind < len(parsed) and count != 0 and parsed[ind] == ')':
                    count-=1
                if ind < len(parsed) and parsed[ind] == '(':
                    count+=1
                ind+=1
            ind -= 1
        ind += 1

    # After iterating whole parsed SQL, adding tableNode to the child of current node.
    if len(current_node.child) >=1:
        for node in current_node.child:
            for table_Node in tableNode_list:
                node.child.append(table_Node)
    else:
        for table_Node in tableNode_list:
                current_node.child.append(table_Node)
    if isaggr:
        temp = Node(aggr)
        temp.child.append(parent_node)
        parent_node = temp

    # returning parent node or can say root node.
    return parent_node
 
# print the graph
def print_graph(root):
    if len(root.child) == 0:
        return
    queue = []
 
    queue.append(root)
 
    while len(queue) > 0:
        node = queue.pop(0)
        print(node.key_ele + ':  [', end="")
        i = 1
        for ele in node.child:
            if i < len(node.child):
                print(ele.key_ele + '; ')
            else:
                print(ele.key_ele + ']')
            i += 1
            queue.append(ele)
        if len(node.child) == 0:
            print(']')
 
       
# main function
def main2(query, dict_of_cte_table):
    global is_cte_in_main
    
    # Preprocessing the query
    query = query.replace('\n', ' ').replace(', ', ',').replace(',', ', ')
    original_query = query

    # if check_syntax(query, 0):
    #     flash("SQL Syntax Error:", "error")
    #     return render_template("SQLViz.html")

    try:
        # Making the parsed SQL.
        parsed = query.split()
        
        list_of_cte = []
        # Creating Digraph.
        graph = Digraph()

        # Parsing Common Table Expressions (CTEs)
        # For CTE, approach goes like: -
        # CTE starts with 'WITH' clause
        # all 'select' clauses replace with 'WITHSELECT' clause
        # all 'UNION' clauses replace with 'WITHUNION' clause
        # such that during iterating time, it should be poosible to know
        # wheter the query is part of CTE or main query.
        i = 0
        while i < len(parsed):
            if parsed[i].upper() == 'WITH':
                cte_str = 'CTE -'
                i += 1
                while i < len(parsed) and parsed[i].upper() != 'AS':
                    cte_str += ' ' + parsed[i]
                    i += 1
                cte_node = Node(cte_str)
                list_of_cte.append(cte_node)
                while i < len(parsed) and parsed[i] not in {')', '),'}:
                    if parsed[i].upper() == 'SELECT':
                        parsed[i] = 'WITHSELECT'
                    if parsed[i].upper() == 'UNION':
                        parsed[i] = 'WITHUNION'
                    i += 1
                if parsed[i] in {')', '),'}:
                    if parsed[i] == '),':
                        parsed.insert(i + 1, 'WITH')
                    parsed[i] += 'WITHEND'
            i += 1
        list_of_main_root = []
        root = Node('Null')
        ind_of_cte = 0
        cte_root = Node('CTE')
        is_main_root = False
        is_create_node = False
        is_cte = False

        # Main parsing logic
        # Based on 'create', 'select', 'Union', 'WITHSELECT' and 'WITHUNION'clause
        # the function sql_to_graph call will be made, accordingly 
        # also knowing whether it is a CTE or main query.
        i = 0
        while i < len(parsed):

            # Based on 'Create' clause
            # Storing the table which is created or replaced.
            # Basically iterating till 'AS' clause.
            if parsed[i].upper() == 'CREATE':
                is_create_node = True
                create_node = Node(parsed[i].upper())
                i += 1
                while parsed[i].upper() != 'TABLE':
                    create_node.key_ele += ' ' + parsed[i].upper()
                    i += 1
                create_node.key_ele += ' ' + parsed[i].upper() + '\n'
                i += 1
                while parsed[i].upper() != 'AS':
                    if parsed[i][-1] == ',':
                        create_node.key_ele += parsed[i] + '\n'
                    else:
                        create_node.key_ele += parsed[i] + ' '
                    i += 1

            # Based on 'Select' Clause
            # calling the sql_to_graph function
            # making it root node.
            if parsed[i].upper() == 'SELECT':
                if i == 0 or (i != 0 and parsed[i - 1] != '('):
                    root = Node('Null')
                    root = sql_to_graph(parsed, root, i, list_of_cte, dict_of_cte_table)
                    print_graph(root)
                    is_main_root = True
                    list_of_main_root.append(root)

            # Based on 'UNION' clause
            # calling the sql_to_graph function
            # making it the root node, and previous root node as it child.
            # AFter UNION or UNION ALL clauses new query start, 
            # calling sql_to_graph function for that query
            # making it the child of root node.
            elif parsed[i].upper() == 'UNION':
                union_node = Node('UNION ALL' if parsed[i + 1].upper() == 'ALL' else 'UNION')
                union_node.child.append(root)
                root = union_node
                root1 = Node('Null')
                root1 = sql_to_graph(parsed, root1, i + 1 if parsed[i + 1].upper() != 'ALL' else i + 2, list_of_cte, dict_of_cte_table)
                i += 1 if parsed[i + 1].upper() != 'ALL' else 2
                root.child.append(root1)

            # Same as 'select' clause
            # But It is the part of CTE.
            elif parsed[i] == 'WITHSELECT':
                root = Node('Null')
                parsed[i] = 'SELECT'
                root = sql_to_graph(parsed, root, i, list_of_cte, dict_of_cte_table)
                is_cte = True

            # Same as 'UNION' clause
            # But it is the part of CTE.
            elif parsed[i] == 'WITHUNION':
                parsed[i] = 'UNION'
                union_node = Node('UNION ALL' if parsed[i + 1].upper() == 'ALL' else 'UNION')
                union_node.child.append(root)
                root = union_node
                root1 = Node('Null')
                parsed[i + 1 if parsed[i + 1].upper() != 'ALL' else i + 2] = 'SELECT'
                root1 = sql_to_graph(parsed, root1, i + 1 if parsed[i + 1].upper() != 'ALL' else i + 2, list_of_cte, dict_of_cte_table)
                i += 1 if parsed[i + 1].upper() != 'ALL' else 2
                root.child.append(root1)

            # At the end of CTE, making another node, having value 'CTE'
            # All the CTE root node will be child of the above node. 
            elif parsed[i] in {')WITHEND', '),WITHEND'}:
                list_of_cte[ind_of_cte].child.append(root)
                root = list_of_cte[ind_of_cte]
                cte_root.child.append(root)
                ind_of_cte += 1

            i += 1

        # If main query is not there, than root will CTE.
        if not is_main_root:
            root = cte_root

        # If 'Create' clause is there, it will be the root node.
        if is_create_node:
            create_node.child.append(root)
            root = create_node

        # If CTE is there, but not used in main query,
        # then it will aslo visulaize as separate node.
        if not is_cte_in_main and is_cte and is_main_root:
            cte_root.visualize(graph)

        print_graph(root)
        root.visualize(graph)
        graph.render('node_structure2', format='png', cleanup=True)
        
        return 'node_structure2.png'

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
 
if __name__ == '__main__':
    query = '''
    CREATE OR REPLACE TABLE bigdata-user.bk1_kim.`bd230841_20230407_batt_usage` AS
WITH mcc AS ( SELECT DISTINCT
mcc_cd,
mnc_cd,
rgn_cd_nm,
cnty_nm,
tco_nm
FROM bigdata-platform-data.bod_000.vf00_tco_cnty_rel  ),
tab1 AS ( SELECT
generation_timestamp,
UPPER(cmp.un) AS p_un,
UPPER(bas.un) AS r_un,
cmp.rand_yn,
bas.agree_yn,
cmp.device_model,
CASE
WHEN m.dvc_gp_nm = 'galaxy s23' THEN 's23'
WHEN m.dvc_gp_nm = 'galaxy s23 plus' THEN 's23p'
WHEN m.dvc_gp_nm = 'galaxy s23 ultra' THEN 's23u'
WHEN m.dvc_gp_nm LIKE 'galaxy z flip 4%' THEN 'flip4'
WHEN m.dvc_gp_nm LIKE 'galaxy z fold 4%' THEN 'fold4'
END AS model_nm,
cmp.yymmddcrt,
mcc.cnty_nm,
CASE
WHEN mcc.rgn_cd_nm = 'europe' THEN '3 europe'
WHEN mcc.rgn_cd_nm = 'north america' THEN '2 north america'
WHEN mcc.rgn_cd_nm = 'korea' THEN '1 korea'
END AS rgn_nm,
SAFE_CAST(JSON_EXTRACT_SCALAR(cmp.custom_value, '$.scron_batd') AS NUMERIC) AS scron_batd,
SAFE_CAST(JSON_EXTRACT_SCALAR(cmp.custom_value, '$.scroff_batd') AS NUMERIC) AS scroff_batd,
FROM bigdata-dqa-data.mobile_udc.to_udc_power AS cmp
INNER JOIN mcc
ON (SAFE_CAST(cmp.mcc AS INT64) = mcc.mcc_cd AND SAFE_CAST(cmp.mnc AS INT64) = mcc.mnc_cd)
INNER JOIN bigdata-platform-data.bup_906_mart.dvc_gp_bas AS m ON (cmp.device_model = m.dvc_modl_id)
LEFT JOIN
bigdata-dqa-data.dqa_public_data.tw_term_agree_dvc_bas AS bas
ON
(cmp.un = bas.rand_id AND SUBSTR(cmp.device_model, 1, 7) = SUBSTR(bas.device_model, 1, 7)
AND bas.agree_yn = 'y')
WHERE
1 = 1
AND cmp.p_yymmddval BETWEEN '2023-03-26' AND '2023-04-08'
AND cmp.yymmddcrt BETWEEN '2023-03-27' AND '2023-04-02'
AND m.dvc_tp_nm = 'smart phone'
AND (m.dvc_gp_nm LIKE '%s23%' OR m.dvc_gp_nm LIKE '%z f% 4%')
AND cmp.feature IN ('batr')
AND (JSON_EXTRACT_SCALAR(cmp.custom_value, '$.scron_batd') IS NOT NULL
OR JSON_EXTRACT_SCALAR(cmp.custom_value, '$.scroff_batd') IS NOT NULL)
AND UPPER(cmp.testd) NOT IN ('dev', 'dev_tool', 'dev_set', 'retail', 'itracker_ut')
AND cmp.testd IS NOT NULL
AND UPPER(cmp.logging_version) NOT IN ('test_version')
AND cmp.logging_version IS NOT NULL
AND REGEXP_CONTAINS(cmp.un, '^[a-za-z0-9]+$')
AND REGEXP_CONTAINS(cmp.firmware_version, '^[a-za-z0-9]+$')
AND REGEXP_CONTAINS(cmp.device_model, '^[a-za-z0-9-]+$')
ORDER BY cmp.un, yymmddcrt ),
tab_un AS ( SELECT
ROW_NUMBER() OVER (PARTITION BY IFNULL(r_un, p_un), yymmddcrt ORDER BY generation_timestamp DESC) AS rn,
IFNULL(r_un, p_un) AS un,
*
FROM tab1
WHERE
1 = 1
AND (rand_yn = 'n' OR rand_yn IS NULL OR rand_yn = '' OR (rand_yn = 'y' AND agree_yn = 'y')) )
SELECT * EXCEPT (rn)
FROM tab_un
WHERE rn = 1
ORDER BY un, yymmddcrt


    '''
    main2(query)
