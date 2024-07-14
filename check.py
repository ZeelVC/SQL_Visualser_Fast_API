class Node:
    def __init__(self, value):
        self.key_ele = value
        self.child = []

def main(query):
    parsed = query.replace('\n', ' ')
    parsed = parsed.replace(', ', ',')
    parsed = parsed.replace(',', ', ').split()
    print(parsed)
    list_of_cte = []
    i = 0
    while i < len(parsed):
        if parsed[i].upper() == 'WITH':
            str = 'CTE -'
            i+=1
            while i < len(parsed) and parsed[i] != 'AS':
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
    #print("List of CTE: - ")
    #for cte in list_of_cte:
    #z    print(cte.key_ele[6:] + '\n')
if __name__ == '__main__':
    query = "WITH t1 AS ( SELECT country,yyyymm,COUNT(DISTINCT duid) AS dvc_cnt_all, FROM bigdata-user.kiseok1035_oh.`tvon_yyyymm` WHERE country IN ('kr', 'us') GROUP BY 1,2 UNION ALL SELECT 'glb' AS country, yyyymm, COUNT(DISTINCT duid) AS dvc_cnt_all, FROM bigdata-user.kiseok1035_oh.`tvon_yyyymm` GROUP BY 1, 2 ) SELECT op1.OrderID, op1.ProductID as p1, op2.ProductID as p2 FROM ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op1 JOIN ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op2 ON op1.OrderID = op2.OrderID AND op1.ProductID > op2.ProductID )"

    #query = "WITH t1 AS ( SELECT country, yyyymm, COUNT(DISTINCT duid) AS dvc_cnt_all, FROM bigdata-user.kiseok1035_oh.`tvon_yyyymm` WHERE country IN ('kr', 'us') GROUP BY 1, 2 UNION ALL SELECT 'glb' AS country, yyyymm, COUNT(DISTINCT duid) AS dvc_cnt_all, FROM bigdata-user.kiseok1035_oh.`tvon_yyyymm` GROUP BY 1, 2 ), t2 AS ( SELECT country, yyyymm, control_ui, COUNT(DISTINCT duid) AS dvc_cnt, SUM(event_cnt) AS event_cnt, FROM bigdata-user.kiseok1035_oh.`control_ui_yyyymm` WHERE country IN ('kr', 'us') GROUP BY 1, 2, 3 UNION ALL SELECT 'glb' AS country, yyyymm, control_ui, COUNT(DISTINCT duid) AS dvc_cnt, SUM(event_cnt), FROM bigdata-user.kiseok1035_oh.`control_ui_yyyymm` GROUP BY 1, 2, 3 ) SELECT op1.OrderID, op1.ProductID as p1, op2.ProductID as p2 FROM ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op1 JOIN ( SELECT DISTINCT OrderID, ProductID FROM OrderLines ) op2 ON op1.OrderID = op2.OrderID AND op1.ProductID > op2.ProductID )"

    main(query)
