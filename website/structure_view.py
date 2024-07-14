import sqlparse
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
    tableNode = Node('Null')

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
            tmp = Node('SELECT')
            j = ind + 1
            str = 'SELECT'
            aggr = 'AGGREGATE'
            isaggr = False
            while parsed[j].upper() != 'FROM':

                # Checking for aggreagate function.
                if aggregate(parsed[j].upper()):
                    isaggr = True
                    break
                j+=1
            ind = j - 1
            #tmp.key_ele = str
            #parent_node = tmp
            #current_node = parent_node

 
        # From clause condition
        # Iterating to the parsed SQL, whenevr encounter the 'from' clause
        # make it the table node and parent node and current node is still the same.
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
                '''tableNode = Node(parsed[ind + 1])
                j = ind + 2
                str = parsed[ind + 1]
                while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'WHERE' and parsed[j].upper() != 'JOIN' and parsed[j].  upper() != 'GROUP' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT' and parsed[j].upper() != 'UNION':
                    str+=' ' + parsed[j]
                    j+=1
                tableNode.key_ele = str
                '''
                tableNode = Node(parsed[ind + 1])
                j = ind + 1
                str = '' 
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
                            #print("visited")
                
 

        # Where clause condition
        # Iterating the parsed SQL, whenever encounter 'where' clause
        # Making it the current node and child of parent node, parent node stills remain the same.

        elif clause.upper() == 'WHERE':
            if parsed[ind + 1] == '(':
                #temp = Node('WHERE')
                #current_node.child.append(temp)
                #current_node = temp
                ind+=1
                continue
            else:
                j = ind + 1
                str = 'WHERE'
                '''while j < len(parsed) and parsed[j] != '(' and parsed[j].upper() != 'JOIN' and parsed[j].upper() != 'GROUP':
                    str += ' ' + parsed[j]
                    j+=1
                '''
                #temp = Node(str)
                #current_node.child.append(temp)
                #current_node = temp
 
 
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
            str = f'{join_type} JOIN'
            j = ind + 1
            second_table = ''
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
            '''while parsed[j] != 'ON':
                j+=1
            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'GROUP' and parsed[j].upper() != 'JOIN':
                str += ' ' + parsed[j]
                j+=1
            '''
            if parent_node.key_ele == 'Null':
                temp = Node(str)
                parent_node = temp
                current_node = temp
            else:
                temp = Node(str)
                temp.child.append(parent_node)
                parent_node = temp    
            
            # If there is no sub_queries between join and on clause, 
            # adding the table node as a child of parent node.
            if parsed[ind + 1] != '(':
                temp = Node(second_table)
                parent_node.child.append(temp)
                for table_name in list_of_cte_table:
                    temp.child.append(table_name)
 
        #group by condition
        elif clause.upper() == 'GROUP':
            j = ind + 2
            str = 'GROUP BY'
            '''while j < len(parsed) and parsed[j].upper() != 'HAVING' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT':
                str+=' ' + parsed[j]
                j+=1
            '''
            #temp = Node(str)
            #temp.child.append(parent_node)
            #parent_node = temp
 
        #Having condition
        elif clause.upper() == 'HAVING':
            j = ind + 1
            str = 'HAVING'
            '''while j < len(parsed) and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT':
                str+=' ' + parsed[j]
                j+=1
            '''
            #temp = Node(str)
            #temp.child.append(parent_node)
            #parent_node = temp
       
        #Order by condition
        elif clause.upper() == 'ORDER':
            j = ind + 2
            str = 'ORDER BY'
            '''while j < len(parsed) and parsed[j].upper() != 'LIMIT':
                str+=' ' + parsed[j]
                j+=1
            '''
            #temp = Node(str)
            #temp.child.append(parent_node)
            #parent_node = temp
 
        #LIMIT condition
        elif clause.upper() == 'LIMIT':
            j = ind + 1
            str = 'LIMIT'
            '''while j < len(parsed):
                str+=' ' + parsed[j]
                j+=1
            '''
            #temp = Node(str)
            #temp.child.append(parent_node)
            #parent_node = temp
 
        # subquery conditon
        # Creating Subquery node and calling the same function.
        # On the basis of subquery is starting after which clause,
        # adding Subquery node accordingly: - 
        # In case of join, add the subquery to the child of parent node
        # while in rest cases to the child of current node
        elif clause == '(' and parsed[ind + 1].upper() == 'SELECT':
            root_subquery = Node('Null')
            '''j = ind + 2
            str = 'SELECT'
            while parsed[j].upper() != 'FROM':
                str+=' ' + parsed[j]
                j+=1
            root_subquery.key_ele = str
            '''
            
            root_subquery = sql_to_graph(parsed, root_subquery, ind + 1, list_of_cte, dict_of_cte_table)
            
            tmp = Node('Subquery')
            if parsed[ind - 1].upper() in {'FROM', 'WHERE', 'AND', 'OR', '=', '>', '<', 'IN', 'LIKE', 'AS', '!=', 'EXISTS'}:
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
                if ind < len(parsed) and count != 0 and parsed[ind] == ')':
                    count-=1
                if ind < len(parsed) and parsed[ind] == '(':
                    count+=1
                ind+=1
            ind-=1
        ind += 1

    # After iterating whole parsed SQL, adding tableNode to the child of current node.
    if current_node.key_ele == 'Null':
        parent_node = tableNode
    else:
        current_node.child.append(tableNode)


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
 
# check_syntax function is temporarily created for
# checking the input SQL whether a valid SQL or not.

def check_syntax(query, ind):   
    if query[ind : ind + 6].upper() != 'SELECT':
        return True
    while ind < len(query):
        if query[ind : ind + 6].upper() == 'SELECT':
            if ind + 6 > len(query):
                print(1)
                return True
            if query[ind + 6] != ' ':
                print(2)
                return True
            keywords = ('FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT')

            if any(query[ind+6:ind+len(keyword)].upper() == keyword for keyword in keywords):
                print(3)
                return True
            j = ind+6
            while query[j:j+4] != 'FROM':
                if query[j] == ',':
                    if query[j + 1] != ' ':
                        print(29)
                        return True
                j+=1
        elif query[ind:ind+4].upper() == 'FROM':
            if ind + 4 > len(query) or ind+5 > len(query):
                print(4)
                return True
            if query[ind+4] != ' ':
                print(5)
                return True
            keywords = ('FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT')

            if any(query[ind+4:ind+4+len(keyword)].upper() == keyword for keyword in keywords):
                print(6)
                return True
        elif query[ind] == '(' and query[ind+1] == ' ':
            if (query[ind-2:ind] != ', ' and query[ind-3:ind].upper() not in ('AVG', 'MIN', 'MAX', 'SUM', 'COUNT')):
                if ind+1 > len(query):
                    print(30)
                    return True
                if query[ind+1] != ' ':
                    print(31)
                    return True
                if query[ind+2:ind+8].upper() != 'SELECT':
                    print(32)
                    return True 
                count = 1
                j = ind + 1
                while j < len(query) and count != 0:
                    if count != 0 and query[j] == ')' and query[j - 1] == ' ':
                        count -= 1
                    elif query[j] == '(' and query[j + 1] == ' ':
                        count += 1
                    j+=1
                if count != 0:
                    print(33)
                    return True
        elif query[ind:ind+5].upper() == 'WHERE':
            if ind + 5 > len(query):
                print(7)
                return True
            if query[ind+5] != ' ':
                print(8)
                return True
            valid_keywords = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+5:ind+len(keyword)+5].upper() == keyword for keyword in valid_keywords):

                print(9)
                return True
        elif query[ind : ind+4].upper() == 'JOIN':
            if ind + 4 > len(query):
                print(17)
                return True
            if query[ind+4] != ' ':
                print(18)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+4:ind+4+len(keyword)].strip().upper() == keyword for keyword in keywords_to_check):
                print(19)
                return True
        elif query[ind:ind+3].upper()=='AND':
            if ind + 3 > len(query):
                print(10)
                return True
            if query[ind+3] != ' ':
                print(11)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+3:ind+3+len(keyword)].strip().upper() == keyword for keyword in keywords_to_check):
                print(12)
                return True
        elif (query[ind:ind+5].upper() =='ORDER' or query[ind:ind+5].upper() == 'GROUP') and query[ind+6 : ind+8]=='BY':
            if ind + 5 > len(query):
                print(13)
                return True
            if query[ind+5] != ' ':
                print(14)
                return True
            if query[ind+6:ind+8] != 'BY':
                print(15)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+5:ind+5+len(keyword)].strip().upper() == keyword for keyword in keywords_to_check):
                print(16)
                return True
        elif (query[ind:ind+2].upper() == 'OR' or query[ind:ind+2].upper() =='ON') and query[ind + 2] == ' ' and query[ind - 1] == ' ':
            if ind + 2 > len(query):
                print(26)
                return True
            if query[ind+2] != ' ':
                print(27)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+2:ind+2+len(keyword)].strip().upper() == keyword for keyword in keywords_to_check):
                print(28)
                return True
        elif query[ind:ind+6].upper() == 'HAVING':
            if ind + 6 > len(query):
                print(20)
                return True
            if query[ind + 6] != ' ':
                print(21)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            if any(query[ind+6:ind+10].strip().upper() == keyword for keyword in keywords_to_check) or \
            any(query[ind+6:ind+12].strip().upper() == keyword for keyword in keywords_to_check):
                print(22)
                return True
        elif query[ind:ind+5].upper() == 'LIMIT':
            if ind + 5 > len(query):
                print(23)
                return True
            if query[ind+5] != ' ':
                print(24)
                return True
            keywords_to_check = ['FROM', 'SELECT', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'LIMIT']

            substring = query[ind+5:ind+12].strip().upper()  # Adjusted to cover the longest keyword length

            if any(substring.startswith(keyword) for keyword in keywords_to_check):
                print(25)
                return True
        ind+=1

    return False


# main function
def main1(query, dict_of_cte_table):
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
        #print(parsed)
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
        graph.render('node_structure1', format='png', cleanup=True)
        
        return 'node_structure1.png'

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
    main1(query)
