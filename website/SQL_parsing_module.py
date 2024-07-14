import re
import sqlparse

def format_sql_query(query):
    # Remove comments
    query = re.sub(r'--.*?(\n|$)', '\n', query)

    # Format CTE
    def format_cte(match):
        cte_name = match.group(1)
        cte_query = match.group(2).strip()
        # Ensure proper spacing around parentheses for CTE
        cte_query = re.sub(r'\(\s*', '( ', cte_query)
        cte_query = re.sub(r'\s*\)', ' )', cte_query)
        # Handle parentheses on new lines for CTE
        cte_query = re.sub(r'^\s*\(', '( ', cte_query, flags=re.MULTILINE)
        cte_query = re.sub(r'\)\s*$', ' )', cte_query, flags=re.MULTILINE)
        return f"WITH {cte_name} AS (\n    {cte_query}\n)"

    cte_pattern = r'WITH\s+(\w+)\s+AS\s*\((.*?)\)'
    query = re.sub(cte_pattern, format_cte, query, flags=re.DOTALL | re.IGNORECASE)

    # Format subqueries
    def format_subquery(match):
        subquery = match.group(1).strip()
        return f"( {subquery} )"

    subquery_pattern = r'\(\s*(SELECT.*?)\s*\)'
    query = re.sub(subquery_pattern, format_subquery, query, flags=re.DOTALL | re.IGNORECASE)

    # Remove parentheses around UNION and UNION ALL
    union_pattern = r'\s*\(\s*(.*?)\s*\)\s*(UNION(?:\s+ALL)?)\s*\(\s*(.*?)\s*\)\s*'
    query = re.sub(union_pattern, r'\n\1\n\2\n\3\n', query, flags=re.DOTALL | re.IGNORECASE)

    # Remove leading parenthesis for UNION and UNION ALL cases
    union_leading_paren_pattern = r'^\s*\(\s*(SELECT.*?)\s*(UNION(?:\s+ALL)?)\s'
    query = re.sub(union_leading_paren_pattern, r'\1\n\2\n', query, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)

    # Handle other parentheses: remove newlines and spaces
    def format_other_parentheses(match):
        content = match.group(1)
        # Remove newlines and extra spaces
        content = re.sub(r'\s+', ' ', content)
        return f"({content.strip()})"

    other_parentheses_pattern = r'\((?!\s*SELECT)(.*?)\)'
    query = re.sub(other_parentheses_pattern, format_other_parentheses, query, flags=re.DOTALL)

    # Move closing parentheses to the end of the previous line
    query = re.sub(r'\n\s*\)', ')', query)

    # Remove extra newlines and spaces
    query = re.sub(r'\n\s*\n', '\n', query)
    query = re.sub(r'^\s+', '', query, flags=re.MULTILINE)

    return query.strip()

# make_sure_CTE_format function check the proper format of parenthesis,
# CTE must be have space inside the parenthesis.
def make_sure_CTE_format(query):
    new_query = ''
    i = 0
    while i < len(query):
        if query[i:i+4].upper() == 'WITH':
            count = 1
            while i < len(query) and query[i] != '(':
                new_query += query[i]
                i += 1 
            new_query+=query[i]
            i+=1
            while i < len(query) and count != 0:
                if query[i] == ')' and count != 0:
                    count -= 1
                    if count == 0:
                        new_query += '\n   ' + query[i]
                        print(str(i) + '-----------------------' + ' ' + query[i])
                        if query[i:i+2] == '),':
                            i+=1
                            count = 1
                            while i < len(query) and query[i] != '(':
                                new_query += query[i]
                                i += 1 
                            new_query+=query[i]
                        else:
                            break
                    else:
                        new_query += query[i]
                elif query[i] == '(':
                    count += 1
                    new_query += query[i]
                else:
                    new_query += query[i]
                
                i+=1
        else:
            new_query += query[i]
        i+=1

    return new_query

# make_sure_sub_foramt function check the format of parenthesis for sub_query,
# sub_query must have the space insidde parenthesis.
def make_sure_sub_format(query):
    new_query = ''
    i = 0
    while i < len(query):
        if query[i] == '(' and query[i+2:i+8].upper() == 'SELECT':
            new_query += query[i]
            i += 1
            count = 1
            while i < len(query) and count != 0:
                if query[i] == ')' and count != 0:
                    count -= 1
                    if count == 0:
                        new_query += ' ' + query[i]
                        break
                    else:
                        new_query += query[i]
                elif query[i] == '(':
                    count += 1
                    new_query += query[i]
                else:
                    new_query += query[i]
                i+=1
        else:
            new_query += query[i]
        i+=1

    return new_query

def sql_to_dict(sql_input):
    # Split the input into individual queries
    queries = sql_input.split(';')
    
    # Initialize an empty dictionary
    query_dict = {}
    
    # Counter for numbering the queries
    counter = 1
    
    # Process each query
    for query in queries:
        # Strip whitespace and newlines from the beginning and end of the query
        stripped_query = query.strip()
            
        # If the stripped query is not empty, format it and add it to the dictionary
        if stripped_query and stripped_query[0:4].upper() != 'DROP' and stripped_query[0:7].upper() != 'DECLARE':
            formatted_query = sqlparse.format(stripped_query)
            formatted_query = format_sql_query(formatted_query)
            formatted_query = make_sure_CTE_format(formatted_query)
            formatted_query = make_sure_sub_format(formatted_query)
            #print(formatted_query)
            query_dict[counter] = formatted_query
            counter += 1
    
    return query_dict


# Example usage:
sql_input = """
SELECT *
FROM employee
WHERE salary > (SELECT AVG(salary) 
                                FROM employee 
                                WHERE department_id = employee.department_id)
AND employee_id != (SELECT todid 
                                      FROM department 
                                      WHERE department.department_id = employee.department_id)

"""

#sql_input = sqlparse.format(sql_input)
result = sql_to_dict(sql_input)

# Print the resulting dictionary
for key, value in result.items():
    print(f"Query {key}:")
    print(value)
    print()