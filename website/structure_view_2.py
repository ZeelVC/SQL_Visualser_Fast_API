import sqlparse
from graphviz import Digraph
from flask import flash, render_template
 
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
 
def aggregate(str):
    present = False
    if str[0] == 'M' and str[1] == 'I' and str[2] == 'N' and str[3] == '(':
        present = True
    elif str[0] == 'M' and str[1] == 'A' and str[2] == 'X' and str[3] == '(':
        present = True
    elif str[0] == 'S' and str[1] == 'U' and str[2] == 'M' and str[3] == '(':
        present = True
    elif str[0] == 'A' and str[1] == 'V' and str[2] == 'G' and str[3] == '(':
        present = True
    elif str[0] == 'C' and str[1] == 'O' and str[2] == 'U' and str[3] == 'N' and str[4] == 'T' and str[5] == '(':
        present = True
    return present


def sql_to_graph(parsed, root, ind, list_of_cte):
 
    #maintaining current_node
    current_node = root
    parent_node = root
    tableNode = Node('Null')
    while ind < len(parsed):
        clause = parsed[ind]
        #close bracket code, indication there was a subquery
        if clause == ')' or clause == ')WITHEND' or clause == '),WITHEND' or clause == 'UNION' or clause == 'WITHUNION':
            break
 
        #select condition
        elif clause.upper() == 'SELECT':
            tmp = Node('SELECT')
            j = ind + 1
            str = 'SELECT'
            aggr = 'AGGREGATE'
            isaggr = False
            while parsed[j].upper() != 'FROM':
                if aggregate(parsed[j].upper()):
                    isaggr = True
                    break
                j+=1
            #tmp.key_ele = str
            #parent_node = tmp
            #current_node = parent_node

 
        #From condition
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
                while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'WHERE' and parsed[j].upper() != 'JOIN' and parsed[j].upper() != 'GROUP' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT' and parsed[j].upper() != 'UNION' and parsed[j].upper() != 'WITHUNION' and parsed[j] != ')WITHEND' and parsed[j] != '),WITHEND' and parsed[j].upper() != 'LEFT' and parsed[j].upper() != 'INNER':
                    if parsed[j][len(parsed[j]) - 1] == ',':
                        str += parsed[j]
                        cte_table_name += parsed[j][0 : len(parsed[j]) - 1]
                        tableNode.key_ele = 'SELF JOIN'
                        table = Node(cte_table_name)
                        tableNode.child.append(table)
                        for table_name in list_of_cte:
                            if cte_table_name == table_name.key_ele[6:]:
                                table.child.append(table_name)
                                break
                        cte_table_name = ''
                        str += '\n'
                    else:
                        cte_table_name+=parsed[j]
                        str += ' ' + parsed[j]
                    j+=1
                if tableNode.key_ele == 'SELF JOIN':
                    table = Node(cte_table_name)
                    tableNode.child.append(table)
                    for table_name in list_of_cte:
                        if cte_table_name == table_name.key_ele[6:]:
                            table.child.append(table_name)
                            break
                if tableNode.key_ele != 'SELF JOIN':        
                    tableNode.key_ele = str
                    for table_name in list_of_cte:
                        if cte_table_name == table_name.key_ele[6:]:
                            tableNode.child.append(table_name)
                            break
                
 
        #Where condition
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
 
 
        #Join condition
        elif clause.upper() == 'JOIN':
            str = ''
            if parsed[ind-1].upper() == 'LEFT':
                str += 'LEFT'
            elif parsed[ind-1].upper() == 'RIGHT':
                str += 'RIGHT'
            elif parsed[ind-1].upper() == 'INNER':
                str += 'INNER'
            elif parsed[ind-1].upper() == 'FULL':
                str += 'FULL'
            elif parsed[ind-1].upper() == 'CROSS':
                str += 'CROSS'
            elif parsed[ind-1].upper() == 'SELF':
                str += 'SELF'
            elif parsed[ind-1].upper() == 'OUTER':
                str += 'OUTER'
            str += ' JOIN'
            j = ind + 1
            second_table = ''
            cte_table_name = ''
            list_of_cte_table = []
            while parsed[j].upper() != 'ON':
                if parsed[j][len(parsed[j]) - 1] == ',':
                    second_table += parsed[j]
                    cte_table_name += parsed[j][0 : len(parsed) - 1]
                    for table_name in list_of_cte:
                        if table_name.key_ele[6:] == cte_table_name:
                            list_of_cte_table.append(table_name)
                            break
                    cte_table_name = ''
                else:
                    second_table += ' ' + parsed[j]
                    cte_table_name += parsed[j]
                j+=1
            for table_name in list_of_cte:
                if table_name.key_ele[6:] == cte_table_name:
                    list_of_cte_table.append(table_name)
                    break
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
 
        #subquery
            #in case join, we had to add the subquery to the parent node
            #while in rest cases to current node
        elif clause == '(' and parsed[ind + 1].upper() == 'SELECT':
            root_subquery = Node('Null')
            '''j = ind + 2
            str = 'SELECT'
            while parsed[j].upper() != 'FROM':
                str+=' ' + parsed[j]
                j+=1
            root_subquery.key_ele = str
            '''
            
            root_subquery = sql_to_graph(parsed, root_subquery, ind + 1, list_of_cte)
            
            tmp = Node('Subquery')
            if parsed[ind - 1].upper() == 'FROM' or parsed[ind - 1].upper() == 'WHERE' or parsed[ind - 1].upper() == 'AND' or parsed[ind - 1].upper() == 'OR' or parsed[ind - 1] == '=' or parsed[ind - 1] == '>' or parsed[ind - 1] == '<' or parsed[ind - 1] == 'IN' or parsed[ind - 1] == 'LIKE' or parsed[ind - 1] == 'AS' or parsed[ind - 1] == '!=':
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
    #at last of each adding tableNode as per approach.
    if current_node.key_ele == 'Null':
        parent_node = tableNode
    else:
        current_node.child.append(tableNode)
    #if isaggr:
    #    temp = Node(aggr)
    #    temp.child.append(parent_node)
    #    parent_node = temp
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
            if query[ind+6 : ind+10].upper() == 'FROM' or query[ind+6 : ind+12].upper() == 'SELECT' or query[ind+6 : ind+11].upper() == 'WHERE' or query[ind+6 : ind+10].upper() == 'JOIN' or query[ind+6 : ind+11].upper() == 'ORDER' or query[ind+6 : ind+11].upper() == 'GROUP' or query[ind+6 : ind+12].upper() == 'HAVING' or query[ind+6 : ind+11].upper() == 'LIMIT':
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
            if query[ind+4 : ind+8].upper() == 'FROM' or query[ind+4 : ind+10].upper() == 'SELECT' or query[ind+4 : ind+9].upper() == 'WHERE' or query[ind+4 : ind+8].upper() == 'JOIN' or query[ind+4 : ind+9].upper() == 'ORDER' or query[ind+4 : ind+9].upper() == 'GROUP' or query[ind+4 : ind+10].upper() == 'HAVING' or query[ind+4 : ind+9].upper() == 'LIMIT':
                print(6)
                return True
        elif query[ind] == '(' and query[ind+1] == ' ':
            if query[ind-2:ind] != ', ' and query[ind-3:ind].upper() != 'AVG' and query[ind-3:ind].upper() != 'MIN' and query[ind-3:ind].upper() != 'MAX' and query[ind-5:ind].upper() != 'COUNT' and query[ind-3:ind].upper() != 'SUM':
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
            if query[ind+5 : ind+9].upper() == 'FROM' or query[ind+5 : ind+11].upper() == 'SELECT' or query[ind+5 : ind+10].upper() == 'WHERE' or query[ind+5 : ind+9].upper() == 'JOIN' or query[ind+5 : ind+10].upper() == 'ORDER' or query[ind+5 : ind+10].upper() == 'GROUP' or query[ind+5 : ind+11].upper() == 'HAVING' or query[ind+5 : ind+10].upper() == 'LIMIT':
                print(9)
                return True
        elif query[ind : ind+4].upper() == 'JOIN':
            if ind + 4 > len(query):
                print(17)
                return True
            if query[ind+4] != ' ':
                print(18)
                return True
            if query[ind+4 : ind+8].upper() == 'FROM' or query[ind+4 : ind+10].upper() == 'SELECT' or query[ind+4 : ind+9].upper() == 'WHERE' or query[ind+4 : ind+8].upper() == 'JOIN' or query[ind+4 : ind+9].upper() == 'ORDER' or query[ind+4 : ind+9].upper() == 'GROUP' or query[ind+4 : ind+10].upper() == 'HAVING' or query[ind+4 : ind+9].upper() == 'LIMIT':
                print(19)
                return True
        elif query[ind:ind+3].upper()=='AND':
            if ind + 3 > len(query):
                print(10)
                return True
            if query[ind+3] != ' ':
                print(11)
                return True
            if query[ind+3 : ind+7].upper() == 'FROM' or query[ind+3 : ind+9].upper() == 'SELECT' or query[ind+3 : ind+8].upper() == 'WHERE' or query[ind+3 : ind+7].upper() == 'JOIN' or query[ind+3 : ind+8].upper() == 'ORDER' or query[ind+3 : ind+8].upper() == 'GROUP' or query[ind+3 : ind+9].upper() == 'HAVING' or query[ind+3 : ind+8].upper() == 'LIMIT':
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
            if query[ind+5 : ind+9].upper() == 'FROM' or query[ind+5 : ind+11].upper() == 'SELECT' or query[ind+5 : ind+10].upper() == 'WHERE' or query[ind+5 : ind+9].upper() == 'JOIN' or query[ind+5 : ind+10].upper() == 'ORDER' or query[ind+5 : ind+10].upper() == 'GROUP' or query[ind+5 : ind+11].upper() == 'HAVING' or query[ind+5 : ind+10].upper() == 'LIMIT':
                print(16)
                return True
        elif (query[ind:ind+2].upper() == 'OR' or query[ind:ind+2].upper() =='ON') and query[ind + 2] == ' ' and query[ind - 1] == ' ':
            if ind + 2 > len(query):
                print(26)
                return True
            if query[ind+2] != ' ':
                print(27)
                return True
            if query[ind+2 : ind+6].upper() == 'FROM' or query[ind+2 : ind+8].upper() == 'SELECT' or query[ind+2 : ind+7].upper() == 'WHERE' or query[ind+2 : ind+6].upper() == 'JOIN' or query[ind+2 : ind+7].upper() == 'ORDER' or query[ind+2 : ind+7].upper() == 'GROUP' or query[ind+2 : ind+8].upper() == 'HAVING' or query[ind+2 : ind+7].upper() == 'LIMIT':
                print(28)
                return True
        elif query[ind:ind+6].upper() == 'HAVING':
            if ind + 6 > len(query):
                print(20)
                return True
            if query[ind + 6] != ' ':
                print(21)
                return True
            if query[ind+6 : ind+10].upper() == 'FROM' or query[ind+6 : ind+12].upper() == 'SELECT' or query[ind+6 : ind+11].upper() == 'WHERE' or query[ind+6 : ind+10].upper() == 'JOIN' or query[ind+6 : ind+11].upper() == 'ORDER' or query[ind+6 : ind+11].upper() == 'GROUP' or query[ind+6 : ind+12].upper() == 'HAVING' or query[ind+6 : ind+11].upper() == 'LIMIT':
                print(22)
                return True
        elif query[ind:ind+5].upper() == 'LIMIT':
            if ind + 5 > len(query):
                print(23)
                return True
            if query[ind+5] != ' ':
                print(24)
                return True
            if query[ind+5 : ind+9].upper() == 'FROM' or query[ind+5 : ind+11].upper() == 'SELECT' or query[ind+5 : ind+10].upper() == 'WHERE' or query[ind+5 : ind+9].upper() == 'JOIN' or query[ind+5 : ind+10].upper() == 'ORDER' or query[ind+5 : ind+10].upper() == 'GROUP' or query[ind+5 : ind+11].upper() == 'HAVING' or query[ind+5 : ind+10].upper() == 'LIMIT':
                print(25)
                return True
        ind+=1

    return False


# main function
def main1(query):
    query = query.replace('\n', ' ')
    query = query.replace(', ', ',')
    query = query.replace(',', ', ')
    #if check_syntax(query, 0):
    #    print('error')
    #    flash("SQL Syntax Error:", "error")
    #    return render_template("SQLViz.html")
        #return
    try:
        #query = "SELECT p1, p2, count(*) as numorders FROM ( SELECT op1.OrderID, op1.ProductID as p1, op2.ProductID as p2 FROM ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op1 JOIN ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op2 ON op1.OrderID = op2.OrderID AND op1.ProductID > op2.ProductID ) combinations JOIN ( SELECT job_address FROM job ) job ON salary_join GROUP BY p1, p2 LIMIT 10"
        
        #query = "SELECT emp_name, emp_id, dep_name FroM employee e Join department d ON e.department_id = d.department_id GROUP BY emp_name, emp_id HAVING sum(this) > 10 ORDER BY emp_name desc LIMIT 5"
        #query = "SELECT * FROM ( SELECT job_id FROM job ) employee e WHERE salary = ( SELECT MAX(salary) FROM department d ) JOIN department d ON e.department_id = d.department_id JOIN ( SELECT job_address FROM job ) job ON salary_join GROUP BY p1, p2"
        #query = "SELECT * FROM department d WHERE salary > 30000"
        #query = "SELECT emp_name, emp_id FROM ( SELECT MAX(salary) FROM employee ) combination GROUP BY p1. p1"
        #query = "SELECT op1.OrderID, op1.ProductID as p1, op2.ProductID as p2 FROM ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op1 JOIN ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op2 ON op1.OrderID = op2.OrderID AND op1.ProductID > op2.ProductID )"
        parsed = query.split()
        list_of_cte = []
        i = 0
        while i < len(parsed):
            if parsed[i].upper() == 'WITH':
                str = 'CTE -'
                i+=1
                while i < len(parsed) and parsed[i].upper() != 'AS':
                    str += ' ' + parsed[i]
                    i+=1
                tmp = Node(str)
                list_of_cte.append(tmp)
                while i < len(parsed) and parsed[i] != ')' and parsed[i] != '),':
                    if parsed[i].upper() == 'SELECT':
                        parsed[i] = 'WITHSELECT'
                    if parsed[i].upper() == 'UNION':
                        parsed[i] = 'WITHUNION'
                    i+=1
                if parsed[i] == ')' or parsed[i] == '),':
                    if parsed[i] == '),':
                        parsed.insert(i + 1, 'WITH')
                    parsed[i]+='WITHEND'
            i+=1
        #print(parsed)
        #root = Node('Null')
        #i = 1
        #str = 'SELECT'
        #aggr = 'AGGREGATE'
        #isaggr = False
        #while parsed[i].upper() != 'FROM':
        #    if aggregate(parsed[i].upper()):
        #        isaggr = True
        #        break
        #    i+=1
        #root.key_ele = str
        #root = sql_to_graph(parsed, root, 1)
        #if isaggr:
        #    temp = Node(aggr)
        #    temp.child.append(root)
        #    root = temp
        graph = Digraph()
        list_of_main_root = []
        root = Node('Null')
        i = 0
        ind_of_cte = 0
        cteroot = Node('CTE')
        is_main_root = False
        is_create_node = False
        is_cte_in_main = False
        while i < len(parsed):
            if parsed[i].upper() == 'CREATE':
                is_create_node = True
                CreateNode = Node(parsed[i].upper())
                i+=1
                while parsed[i].upper() != 'TABLE':
                    CreateNode.key_ele+=' ' + parsed[i].upper()
                    i+=1
                CreateNode.key_ele+=' ' + parsed[i].upper() + '\n'
                i+=1
                while parsed[i].upper() != 'AS':
                    if parsed[i][len(parsed[i]) - 1] == ',':
                        CreateNode.key_ele += parsed[i] + '\n'
                    else:
                        CreateNode.key_ele += parsed[i] + ' '
                    i+=1
            if parsed[i].upper() == 'SELECT':
                if i == 0 or (i != 0 and parsed[i - 1] != '('):
                    root = Node('Null')
                    root = sql_to_graph(parsed, root, i, list_of_cte)
                    print_graph(root)
                    is_main_root = True
                    list_of_main_root.append(root)
            elif parsed[i].upper() == 'UNION':
                tmp = Node('UNION ALL')
                if parsed[i + 1].upper() != 'ALL': 
                    tmp.key_ele = 'UNION'
                tmp.child.append(root)
                root = tmp
                root1 = Node('Null')
                if parsed[i + 1].upper() != 'ALL':
                    root1 = sql_to_graph(parsed, root1, i + 1, list_of_cte)
                    i+=1
                else:
                    root1 = sql_to_graph(parsed, root1, i + 2, list_of_cte)
                    i+=2
                root.child.append(root1)
            elif parsed[i] == 'WITHSELECT':
                root = Node('Null')
                parsed[i] = 'SELECT'
                root = sql_to_graph(parsed, root, i, list_of_cte)
            elif parsed[i] == 'WITHUNION':
                parsed[i] = 'UNION'
                tmp = Node('UNION ALL')
                if parsed[i + 1].upper() != 'ALL': 
                    tmp.key_ele = 'UNION'
                tmp.child.append(root)
                root = tmp
                root1 = Node('Null')
                if parsed[i + 1].upper() != 'ALL':
                    parsed[i+1] = 'SELECT'
                    root1 = sql_to_graph(parsed, root1, i + 1, list_of_cte)
                    i+=1
                else:
                    parsed[i+2] = 'SELECT'
                    root1 = sql_to_graph(parsed, root1, i + 2, list_of_cte)
                    i+=2
                root.child.append(root1)
            elif parsed[i] == ')WITHEND' or parsed[i] == '),WITHEND':
                list_of_cte[ind_of_cte].child.append(root)
                root = list_of_cte[ind_of_cte]
                cteroot.child.append(root)
                ind_of_cte+=1
                
            i+=1
        if is_main_root == False:
            root = cteroot
        if is_create_node == True:
                CreateNode.child.append(root)
                root = CreateNode    
        #if is_cte_in_main == False:
        #    cteroot.visualize(graph)


        print_graph(root)
    
        root.visualize(graph)
        graph.render('node_structure1', format='png', cleanup=True)
        return f'{'node_structure1'}.png'
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
 
if __name__ == '__main__':
    #query = "SELECT * FROM ( SELECT job_id FROM job ) employee e WHERE salary = ( SELECT MAX(salary) FROM department d ) JOIN department d ON e.department_id = d.department_id JOIN ( SELECT job_address FROM job ) job ON salary_join GROUP BY p1, p2"
    #query = "SELECT e.employee_id, e.employee_name, e.salary, d.department_name FROM employee e JOIN department d ON e.department_id = d.department_id WHERE e.salary > ( SELECT AVG(salary) FROM employee WHERE department_id = e.department_id )"

    #query = "SELECT country, product, year, month FROM `bigdata-user.avinash_t`.`BD240662_base` WHERE fold_count IS NOT NULL AND fold_count > 0 AND country IS NOT NULL GROUP BY 1,2,3,4 ORDER BY 1,2,3,4"
    #query = "SELECT country, product, year, month,SUM(fold_count) as fold_count, COUNT(un) as device_count FROM `bigdata-user.avinash_t`.`BD240662_base` WHERE fold_count IS NOT NULL AND fold_count > 0 AND country IS NOT NULL GROUP BY 1,2,3,4 ORDER BY 1,2,3,4"
    #query="SELECT  un FROM `bigdata-dqa-data.mobile_udc`.`to_udc_tsp` WHERE p_yymmddval >= '2021-08-01 AND  REGEXP_CONTAINS(un, '^[A-Za-z0-9]+$') AND mcc in ('410', '411', '412', '413', '414', '450') and feature = 'HKEY' and device_model like any ('%SM-F711%','%SM-F926%','%SM-F721%','%SM-F936%','%SM-F731%','%SM-F946%')"
    query = "Select job_id, salary from job group by 1, 2"
    main1(query)