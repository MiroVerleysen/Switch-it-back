from .Database import Database

class DataRepository:
    @staticmethod
    def json_or_formdata(request):
        if request.content_type == 'application/json':
            gegevens = request.get_json()
        else:
            gegevens = request.form.to_dict()
        return gegevens

    
    #update van 1 sensor
    @staticmethod
    def update_waarde_sensor(id, waarde):
        sql = "Insert into Meetwaarde (sensorid, waarde) values (%s, %s)"
        params = [id, waarde]
        return Database.execute_sql(sql, params)
    
    #alle sensordata ophalen
    @staticmethod
    def read_all_sensors():
        sql = "select * from Meetwaarde"
        return Database.get_rows(sql)

    #laatste waarde van 1 sensor ophalen
    @staticmethod
    def read_sensor_by_id_one(id):
        sql = "SELECT * from Meetwaarde WHERE sensorID = %s order by tijd desc limit 1"
        params = [id]
        return Database.get_rows(sql, params)
    
    #laatste waarden van 1 sensor ophalen
    @staticmethod
    def read_sensor_by_id_recent(id, tijd):
        sql = "SELECT meetingid, sensorid, waarde, date_format(date_add(tijd, interval 30 second),'%Y-%m-%d %H:%i:00') as datum from Meetwaarde WHERE sensorID = %s and tijd >= now() - interval %s hour order by datum asc"
        params = [id, tijd]
        return Database.get_rows(sql, params)

    #ophalen laatste status van 1 actuator
    @staticmethod
    def read_status_actuator_by_id(id):
        sql = "SELECT * from Schakelen WHERE actuatorID = %s order by tijdstip desc limit 1"
        params = [id]
        return Database.get_one_row(sql, params)
        
    #update van 1 actuator
    @staticmethod
    def update_waarde_actuator(id, tijdstip, status):
        sql = "Insert into Schakelen (actuatorid, tijdstip, status) values (%s, %s, %s)"
        params = [id, tijdstip, status]
        return Database.execute_sql(sql, params)

    @staticmethod
    def read_schakelhistorie(kaas):
        sql = "SELECT * from Schakelen WHERE actuatorID = 1 limit %s"
        params = [kaas]
        return Database.get_one_row(sql, params)

    @staticmethod
    def read_gepland(status):
        sql = "SELECT distinct tijdstip FROM Schakelen where status = %s and tijdstip > current_time() order by tijdstip limit 1"
        params = [status]
        return Database.get_rows(sql, params)

    @staticmethod
    def read_gepland_all():
        sql = "SELECT distinct tijdstip, status FROM Schakelen where tijdstip > current_time() order by tijdstip"
        return Database.get_rows(sql)