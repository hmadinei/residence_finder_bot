import psycopg2

class DatabaseHandler:
    def __init__(self, dbname, user, password, host, port=5432):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.dbname = dbname
        
        
    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname, 
                user=self.user, 
                password=self.password, 
                host=self.host, 
                port=self.port
            )
            print("Database connection established.")
        except Exception as e:
            print(f"An error occurred while connecting to the database: {e}")
            self.conn = None

    def query(self, tabel, values):
        if self.conn is None:
            print("Not connected to the database.")
            return None

        try:
            cursor = self.conn.cursor()
            # Query
            
            cursor.execute(f"""SELECT "PlaceCode", "AreasSize", "RateScore", "CapacityBase"
                        FROM {tabel}
                        WHERE "CapacityBase" = %s
                        AND CAST("RateScore" AS FLOAT) >= %s
                        AND CAST(REPLACE("AreasSize", ',', '') AS INTEGER) BETWEEN %s AND %s
                        LIMIT 5""",
                        (values[0], values[1], values[2][0], values[2][1]))
            
            results = cursor.fetchall() 
            self.conn.commit()  
            return results
                
        except Exception as e:
            print(f"An error occurred while executing the query: {e}")
            self.conn.rollback() 


    def llama_query(self, tabel, parameters):
        if self.conn is None:
            print("Not connected to the database.")
            return None

        try:
            cursor = self.conn.cursor()
            conditions = []
            values = []

            # Check for CapacityBase  
            if "CapacityBase" in parameters:
                conditions.append(f'"CapacityBase" = %s')
                values.append(parameters['CapacityBase'])
                
            # Check for CapacityBase  
            if "RateScore" in parameters:
                conditions.append(f'"RateScore" >= %s')
                values.append(parameters['RateScore'])
                
                
            # Check for AreasSize
            if 'AreasSize' in parameters and isinstance(parameters['AreasSize'], tuple):
                conditions.append(f'CAST(REPLACE("AreasSize", \',\', \'\') AS INTEGER) BETWEEN %s AND %s')
                values.extend(parameters['AreasSize'])
                
            
            # query
            query = f"""SELECT "PlaceCode", "AreasSize", "RateScore", "CapacityBase" FROM {tabel}"""

            # Add conditions to query
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " LIMIT 5 "
                
            print(query)

            # Execute the query
            cursor.execute(query, tuple(values))
            
            results = cursor.fetchall() 
            self.conn.commit()  
            return results
                
        except Exception as e:
            print(f"An error occurred while executing the query: {e}")
            self.conn.rollback() 
    
    
    def close(self):
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

# Example usage
if __name__ == "__main__":
    pass
    db_handler = DatabaseHandler('Mori', 'postgres', 'hana2641378', 'localhost')
    db_handler.connect()
    # result = db_handler.query(tabel='tehran_data_jabama', values=[2, 1.4, 300, 1000])
    result = db_handler.llama_query(tabel='tehran_data_jabama', parameters={"CapacityBase": 2,
                                                                        "AreasSize": (300, 10000)
                                                                        })
    
    print(result)
    db_handler.close()
    
    
