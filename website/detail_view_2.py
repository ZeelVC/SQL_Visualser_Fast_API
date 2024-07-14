import sqlparse, re
from graphviz import Digraph
from flask import flash, render_template
#from .logic1 import check_syntax
 
#To create a different for data structure module.
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
 
#To create a different module for aggregate function.
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

#To create a different module for each funtion of sql_to_graph function.
def sql_to_graph(parsed, root, ind, list_of_cte):
 
    #maintaining current_node
    current_node = root
    parent_node = root
    tableNode = Node('0')
    tableNode_list = []
    isaggr = False
    while ind < len(parsed):
        clause = parsed[ind]
        #close bracket code, indication there was a subquery
        if clause == ')' or clause == ')WITHEND' or clause == '),WITHEND' or clause == 'UNION' or clause == 'WITHUNION':
            break

        #select condition
        #Also need to optimise the aggregate function code is there is a space in aggregate function.
        elif clause.upper() == 'SELECT':
            temp = Node('SELECT')
            j = ind + 1
            str = 'SELECT' + '\n\n( '
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
                    str+= key_str + '\n'
                    dict[key_value] = []
                    dict[key_value].append(key_str)
                    key_value+=1
                    key_str = ''
                    aggr+='\n\n'
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
                j+=1
            dict[key_value] = []
            dict[key_value].append(key_str)
            key_value+=1
            key_str = ''
            str += ' )'
            temp.key_ele = str  
            parent_node = temp
            current_node = parent_node
            print(dict)

        #From condition
        elif clause.upper() == 'FROM':
            if parsed[ind + 1] == '(':
                ind+=1
                continue
            else:
                tableNode = Node(parsed[ind + 1])
                j = ind + 1
                str = 'FROM\n\n( ' 
                cte_table_name = ''
                while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'WHERE' and parsed[j].upper() != 'JOIN' and parsed[j].upper() != 'GROUP' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT' and parsed[j].upper() != 'UNION' and parsed[j].upper() != 'WITHUNION' and parsed[j] != ')WITHEND' and parsed[j] != '),WITHEND' and parsed[j].upper() != 'LEFT' and parsed[j].upper() != 'INNER' and parsed[j].upper() != 'SELECT':
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
                    str+= ' )'      
                    tableNode.key_ele = str
                    for table_name in list_of_cte:
                        if cte_table_name == table_name.key_ele[6:]:
                            tableNode.child.append(table_name)
                            break
                tableNode_list.append(tableNode)
 
        #Where condition
        elif clause.upper() == 'WHERE':
            j = ind + 1
            str = 'WHERE' + '\n\n( '
            while j < len(parsed) and parsed[j].upper() != 'JOIN' and parsed[j].upper() != 'GROUP' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT' and parsed[j].upper() != 'UNION' and parsed[j].upper() != 'WITHUNION' and parsed[j] != ')WITHEND' and parsed[j] != '),WITHEND' and parsed[j].upper() != 'SELECT':
                if parsed[j] == ')':
                    break
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
            str += ' JOIN\n\n( '
            j = ind + 1
            second_table = 'FROM\n\n( '
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
            while j < len(parsed) and parsed[j] != ')' and parsed[j] != 'WHERE' and parsed[j].upper() != 'GROUP' and parsed[j].upper() != 'JOIN' and parsed[j].upper() != 'UNION' and parsed[j].upper() != 'WITHUNION' and parsed[j] != ')WITHEND' and parsed[j] != '),WITHEND' and parsed[j].upper() != 'SELECT':
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
 
        #group by condition
        elif clause.upper() == 'GROUP':
            j = ind + 2
            str = 'GROUP BY' + '\n\n( '
            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'HAVING' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT' and parsed[j].upper() != 'UNION' and parsed[j].upper() != 'WITHUNION' and parsed[j] != ')WITHEND' and parsed[j] != '),WITHEND' and parsed[j].upper() != 'SELECT':
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
 
        #Having condition
        elif clause.upper() == 'HAVING':
            j = ind + 1
            str = 'HAVING' + '\n\n( '
            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'ORDER' and parsed[j].upper() != 'LIMIT' and parsed[j].upper() != 'UNION' and parsed[j].upper() != 'WITHUNION' and parsed[j] != ')WITHEND' and parsed[j] != '),WITHEND' and parsed[j].upper() != 'SELECT':
                if parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
       
        #Order by condition
        elif clause.upper() == 'ORDER':
            j = ind + 2
            str = 'ORDER BY' + '\n\n( '
            while j < len(parsed) and parsed[j] != ')' and parsed[j].upper() != 'LIMIT' and parsed[j].upper() != 'UNION' and parsed[j].upper() != 'WITHUNION' and parsed[j] != ')WITHEND' and parsed[j] != '),WITHEND' and parsed[j].upper() != 'SELECT':
                if parsed[j][len(parsed[j]) - 1] == ',':
                    str += parsed[j] + '\n'
                else:
                    str += parsed[j] + ' '
                j+=1
            str += ' )'
            temp = Node(str)
            temp.child.append(parent_node)
            parent_node = temp
 
        #LIMIT condition
        elif clause.upper() == 'LIMIT' and parsed[j].upper() != 'UNION' and parsed[j].upper() != 'WITHUNION' and parsed[j] != ')WITHEND' and parsed[j] != '),WITHEND' and parsed[j].upper() != 'SELECT':
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
 
        #subquery
            #in case join, we had to add the subquery to the parent node
            #while in rest cases to current node
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
            root_subquery = sql_to_graph(parsed, root_subquery, ind + 1, list_of_cte)
            if isaggr:
                temp = Node(aggr)
                temp.child.append(root_subquery)
                root_subquery = temp
            tmp = Node('Subquery')
            if parsed[ind - 1].upper() == 'FROM':
                tableNode.child.append(tmp)
                tmp.child.append(root_subquery)
                tableNode = tmp
            elif parsed[ind - 1].upper() == 'WHERE' or parsed[ind - 1].upper() == 'AND' or parsed[ind - 1].upper() == 'OR' or parsed[ind - 1] == '=' or parsed[ind - 1] == '>' or parsed[ind - 1] == '<' or parsed[ind - 1] == 'IN' or parsed[ind - 1] == 'LIKE' or parsed[ind - 1] == 'AS' or parsed[ind - 1] == '!=':
                for node in current_node.child:
                    if node.key_ele.find('Subquery') != -1:
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
                    count-=1
                if ind < len(parsed) and parsed[ind] == '(':
                    count+=1
                ind+=1
            ind -= 1
        ind += 1
    #at last of each adding tableNode as per approach.
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
def main2(query):
    query = query.replace('\n', ' ')
    query = query.replace(', ', ',')
    query = query.replace(',', ', ')
    query1 = query
    #if check_syntax(query, 0):
     #   flash("SQL Syntax Error:", "error")
      #  return render_template("SQLViz.html")
    query = query1
    try:
        #query = "SELECT p1, p2, count(*) as numorders FROM ( SELECT op1.OrderID, op1.ProductID as p1, op2.ProductID as p2 FROM ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op1 JOIN ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op2 ON op1.OrderID = op2.OrderID AND op1.ProductID > op2.ProductID ) combinations JOIN ( SELECT job_address FROM job ) job ON salary_join GROUP BY p1, p2 LIMIT 10"
        
        #query = "SELECT emp_name, emp_id, dep_name FroM employee e Join department d ON e.department_id = d.department_id GROUP BY emp_name, emp_id HAVING sum(this) > 10 ORDER BY emp_name desc LIMIT 5"
        #query = "SELECT * FROM ( SELECT job_id FROM job ) employee e WHERE salary = ( SELECT MAX(salary) FROM department d ) JOIN department d ON e.department_id = d.department_id JOIN ( SELECT job_address FROM job ) job ON salary_join GROUP BY p1, p2"
        #query = "SELECT * FROM department d WHERE salary > 30000"
        #query = "SELECT emp_name, emp_id FROM ( SELECT MAX(salary) FROM employee ) combination GROUP BY p1. p1"
        #query = "WITH t1 AS ( SELECT country, yyyymm, COUNT(DISTINCT duid) AS dvc_cnt_all, FROM bigdata-user.kiseok1035_oh.`tvon_yyyymm` WHERE country IN ('kr', 'us') GROUP BY 1, 2 UNION ALL SELECT 'glb' AS country, yyyymm, COUNT(DISTINCT duid) AS dvc_cnt_all, FROM bigdata-user.kiseok1035_oh.`tvon_yyyymm` GROUP BY 1, 2 ) SELECT op1.OrderID, op1.ProductID as p1, op2.ProductID as p2 FROM ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op1 JOIN ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op2 ON op1.OrderID = op2.OrderID AND op1.ProductID > op2.ProductID )"
        parsed = query.split()
        #print(parsed)
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
                list_of_cte.append(tmp);
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
        #i = 1
        #str = 'SELECT' + '\n\n( '
        #aggr = 'AGGREGATE \n\n'
        #isaggr = False
        #while parsed[i].upper() != 'FROM':
        #    if aggregate(parsed[i].upper()):
        #        aggr+=parsed[i].upper()+'\n\n'
        #        isaggr = True
        #    elif parsed[i][len(parsed[i]) - 1] == ',':
        #        str += parsed[i] + '\n'
        #    else:
        #        str += parsed[i] + ' '
        #    i+=1
        #str += ' )'
        #root.key_ele = str
        #root = sql_to_graph(parsed, root, 0)
        list_of_main_root = []
        root = Node('Null')
        i = 0
        ind_of_cte = 0
        cteroot = Node('CTE')
        is_main_root = False
        is_create_node = False
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
        #if len(list_of_main_root) > 1:
        #    main_root = Node('Main_Queries_Root')
        #    for roots in list_of_main_root:
        #        main_root.child.append(roots)
        #    root = main_root
        #if isaggr:
        #    temp = Node(aggr)
        #    temp.child.append(root)
        #    root = temp
        
        print_graph(root)
    
        graph = Digraph()
        root.visualize(graph)
        graph.render('node_structure2', format='png', cleanup=True)
        return f'{'node_structure2'}.png'
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
 
if __name__ == '__main__':
    #query = "SELECT country, product, year, month, SUM(fold_count) as fold_count, COUNT(un) as device_count FROM `bigdata-user.avinash_t`.`BD240662_base` WHERE fold_count IS NOT NULL AND fold_count > 0 AND country IS NOT NULL GROUP BY 1,2,3,4 ORDER BY 1,2,3,4"
    #query = "SELECT country, yyyymm, control_ui, COUNT(DISTINCT duid) AS dvc_cnt, SUM(event_cnt) AS event_cnt, FROM bigdata-user.kiseok1035_oh.`control_ui_yyyymm` WHERE country IN ('kr', 'us') GROUP BY 1, 2, 3 UNION ALL SELECT 'glb' AS country, yyyymm, control_ui, COUNT(DISTINCT duid) AS dvc_cnt, SUM(event_cnt), FROM bigdata-user.kiseok1035_oh.`control_ui_yyyymm` GROUP BY 1, 2, 3"
    #query = "SELECT country, yyyymm, control_ui, COUNT(DISTINCT duid) AS dvc_cnt, SUM(event_cnt) AS event_cnt, FROM bigdata-user.kiseok1035_oh.`control_ui_yyyymm` WHERE country IN ('kr', 'us') GROUP BY 1, 2, 3 UNION SELECT * FROM title" 
    #query = "WITH t1 AS ( SELECT country, yyyymm, COUNT(DISTINCT duid) AS dvc_cnt_all, FROM bigdata-user.kiseok1035_oh.`tvon_yyyymm` WHERE country IN ('kr', 'us') GROUP BY 1, 2 UNION ALL SELECT 'glb' AS country, yyyymm, COUNT(DISTINCT duid) AS dvc_cnt_all, FROM bigdata-user.kiseok1035_oh.`tvon_yyyymm` GROUP BY 1, 2 ) SELECT * from t1, job join t1 On job.id = emp.id"
    #query = "WITH t1 AS ( SELECT country, yyyymm, COUNT(DISTINCT duid) AS dvc_cnt_all, FROM bigdata-user.kiseok1035_oh.`tvon_yyyymm` WHERE country IN ('kr', 'us') GROUP BY 1, 2 UNION ALL SELECT 'glb' AS country, yyyymm, COUNT(DISTINCT duid) AS dvc_cnt_all, FROM bigdata-user.kiseok1035_oh.`tvon_yyyymm` GROUP BY 1, 2 ), t2 AS ( SELECT country, yyyymm, control_ui, COUNT(DISTINCT duid) AS dvc_cnt, SUM(event_cnt) AS event_cnt, FROM bigdata-user.kiseok1035_oh.`control_ui_yyyymm` WHERE country IN ('kr', 'us') GROUP BY 1, 2, 3 UNION ALL SELECT 'glb' AS country, yyyymm, control_ui, COUNT(DISTINCT duid) AS dvc_cnt, SUM(event_cnt), FROM bigdata-user.kiseok1035_oh.`control_ui_yyyymm` GROUP BY 1, 2, 3 )"
    #query = "SELECT * FROM job where salary > 30000 and salary < 50000 SELECT * from employee JOIN department ON dep_id == emp_id"
    query = "Select job_id,salary from job group by 1,2"
    main2(query)