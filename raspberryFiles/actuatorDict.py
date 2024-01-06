class ActuatorDict :
    
    __actuators=[]
    
    def __init__(self) -> None:
        #no need of __init__
        pass
    
    def add(self, id:int, name, onoff):
        if (self.get_act(id)== None):
            self.__actuators.append({"index":len(self.__actuators), "id": int(id), "name":name, "onoff":onoff})
        
    def get_act(self, id:int):
        for i in self.__actuators:
            if(i["id"]==id):
                return i
        return None
    
    def set_act(self, index:int, dictio:dict):
        if index!=None and len(dictio)==5:
            dictio.update("index",index)
            self.__actuators[index]=dictio
        else :
            ind=self.get_act(dictio["id"])["index"]

            if "onoff" in dictio: 
                if (dictio["onoff"]=="on" or dictio["onoff"]=="off"): 
                    self.__actuators[ind]["onoff"]=dictio["onoff"] 
                else: 
                    raise TypeError("must be either 'on' or 'off'")
                
                self.__actuators[ind]["wattage"]=dictio["wattage"] if "wattage" in dictio else 1
                self.__actuators[ind]["date"]=dictio["date"] if "date" in dictio else 1
                self.__actuators[ind]["name"]=dictio["name"] if "name" in dictio else 1

    def get_all_id(self):
        return [d['id'] for d in self.__actuators]
# dictionary of actuator with necessary functions to get the data and corelated files