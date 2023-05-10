
import json
import logging
import Ice
import IceStorm

Ice.loadSlice("iceflix.ice")
import IceFlix

DATA_JSON = "../data/data.json"


class Persistence:
    def read_json(self):
        try:
            with open(DATA_JSON,'r') as json_file:
                data = json.load(json_file)
                return data
        except:
            logging.error("Error al leer el fichero json")
            return None
    def write_json(self,data):
        try:
            with open(DATA_JSON,'w') as json_file:
                json.dump(data, json_file)
        except:
            logging.error("Error al escribir el fichero json")

class MediaCatalog(IceFlix.MediaCatalog):

    def __init__(self, auth_service,announcement, catalog_up_pub):
        self.auth_service = auth_service
        self.data_media={}
        self.announcement=announcement
        self.publiser=catalog_up_pub

        self.providers={}
        self.service_id=""
        self.persistence=Persistence()


    def recargar(self):
        self.data_media=self.persistence.read_json()
    
    def providers_up(self,mediaId,ser,current=None):
        self.providers={}
        for id in self.data_media.get("MediaId"):
            if id== mediaId:
                self.providers[mediaId]=ser
            
        
    

    def getTile(self, mediaId, userToken, current=None):

        user=""
        try:
            user = self.auth_service.whois(userToken)
        except:
            raise IceFlix.Unauthorized()
        
        media=IceFlix.Media()
        info=IceFlix.MediaInfo()

        self.data_media = self.persistence.read_json()

        for file in self.data_media.get("Media"):
            if file.get("MediaId") == mediaId:
                media.mediaId=str(mediaId)
                info.name=file.get("Name")
                info.tags=file.get("UserInfo").get("Tags")
        media.info=info
        return media


    def getTilesByName(self, name, exact, current=None):
        
        list_files=[]
        self.data_media = self.persistence.read_json()

        for file in self.data_media.get("Media"):
            if(exact):
                if file.get("Name") == name:
                    list_files.append(file.get("Name"))
            else:
                if name in file.get("Name"):
                    list_files.append(file.get("Name"))  
        return list_files
    
    def getTilesByTags(self, tags, includeAllTags, userToken, current=None):

        user=""
        try:
            user = self.auth_service.whois(userToken)
        except:
            raise IceFlix.Unauthorized()
        
        list_files=[]
        self.data_media = self.persistence.read_json()
        for file in self.data_media.get("Media"):
            tagslower=[]
            for i in range(len(tags)):
                tagslower.append(tags[i].lower())
            userinfo=file.get("UserInfo")
            if userinfo.get("UserName") == user:
                tagsarray=[]
                if includeAllTags:
                    for tag in userinfo.get("Tags"):
                        tagsarray.append(tag.lower())
                        for tagssearch in tagslower:
                            if tagssearch in tagsarray:
                                tagsarray.remove(tagssearch)
                    if len(tagsarray)==0:
                        list_files.append(file.get("Name"))
                else:
                    for tag in userinfo.get("Tags"):
                        for tagssearch in tagslower:
                            if tagssearch in tag.lower():
                                list_files.append(file.get("Name"))
        return list_files
        
    def newMedia(self, mediaId, provider, current=None):

        self.data_media = self.persistence.read_json()
        new_media={"MediaId":mediaId,"Name":mediaId,"Tags":[]}
        self.data_media["Media"].append(new_media)
        self.persistence.write_json(self.data_media)
        return 0
        
    def removeMedia(self, mediaId, provider, current=None):
        self.data_media = self.persistence.read_json()
        for file in self.data_media.get("Media"):
            if file.get("MediaId") == mediaId:
                self.data_media["Media"].remove(file)
                self.persistence.write_json(self.data_media)
        return 0
    def renameTile(self, mediaId, name, adminToken, current=None):

        if self.auth_service.isAdmin(adminToken):
            persistence=Persistence()
            self.data_media = persistence.read_json()
            for file in self.data_media.get("Media"):
                if file.get("MediaId") == mediaId:
                    file["Name"]=name
                    persistence.write_json(self.data_media)
        else:
            logging.info("Admin token incorrecto")
        
        return 0

    def addTags(self, mediaId, tags, userToken, current=None):

        user=""
        try:
            user = self.auth_service.whois(userToken)
        except:
            raise IceFlix.Unauthorized()
        
        
        self.data_media = self.persistence.read_json()
        for file in self.data_media.get("Media"):
            if file.get("MediaId") == mediaId:
                if user==file.get("UserInfo").get("UserName"):
                    for tag in tags:
                        if tag not in file["UserInfo"]["Tags"]:
                            file["UserInfo"]["Tags"].append(tag)
                    self.persistence.write_json(self.data_media)
        return 0
        
    def removeTags(self, mediaId, tags, userToken, current=None):
        
        user=""
        try:
            user = self.auth_service.whois(userToken)
        except:
            raise IceFlix.Unauthorized()
        self.data_media = self.persistence.read_json()
        for file in self.data_media.get("Media"):
            if file.get("MediaId") == mediaId:
                for tag in tags:
                    if tag in file["UserInfo"]["Tags"]:
                        file["UserInfo"]["Tags"].remove(tag)
                self.persistence.write_json(self.data_media)
        return 0
    
        
class Announcement(IceFlix.Annoucement):

    def __init__(self):
        self.catalog_ser={}
        self.auth_ser={}
        self.file_ser={}
    
    def announce(self,service,serviceId,current=None):
        if service.ice_isA("::IceFlix::MediaCatalog"):
            logging.log(f'[Announcement] announce Catalog: {serviceId}')
            if not serviceId in self.catalog_ser:
                self.catalog_ser[serviceId]=IceFlix.MediaCatalogPrx.uncheckedCast(service)
                
        elif service.ice_isA("::IceFlix::Authenticator"):
            logging.log(f'[Announcement] announce Authenticator: {serviceId}')
            if not serviceId in self.auth_ser:
                self.auth_ser[serviceId]=IceFlix.AuthenticatorPrx.uncheckedCast(service)

        elif service.ice_isA("::IceFlix::FileService"):
            logging.log(f'[Announcement] announce File: {serviceId}')
            if not serviceId in self.file_ser:
                self.file_ser[serviceId]=IceFlix.FileServicePrx.uncheckedCast(service)

class FileAvailabilityAnnounce(IceFlix.FileAvailabilityAnnounce):

    def __init__(self,annoucement,catalog):
        self.announce=annoucement
        self.catalogo=catalog

    def announce(self,mediaId,serviceId,current=None):
        if serviceId in self.announce.file_ser:
            print("[FileAvailability] Id servicio {} Id media {}",serviceId,mediaId)
            services=self.announce.file_ser[mediaId]
            self.catalogo.providers_up(mediaId,services)



    
        
class CatalogUpdate():
    def __init__(self,announcement,catalog,service_Id):
        self.service_ID=service_Id
        self.catalogo=catalog
        self.announce=announcement
        self.persistencia=Persistence()

    def renameTile(self, mediaId,  newName,  serviceId,current=None):
        if serviceId != self.service_ID:
            print("[Catalog Update] Actualizando titulo con id {} y nombre {}",mediaId,newName)
            if serviceId in self.announce.catalog_ser:
                files=self.persistencia.read_json()
                self.catalogo.data_media=files
            else:
                print("[Catalog Update] El servicio no esta registrado")
            

    def addTags(self, mediaId, user, tags, serviceId,current=None):
        if serviceId != self.service_ID:
            print("[Catalog Update] Actualizando tags con id {}, usuario {} y tags {}",mediaId,user,tags)
            if serviceId in self.announce.catalog_ser:
                files=self.persistencia.read_json()
                self.catalogo.data_media=files

    def removeTags(self, mediaId,  user,  tags,  serviceId,current=None):
        if serviceId != self.service_ID:
            print("[Catalog Update] Eliminando tags con id {} usuario {} y tags {}",mediaId,user,tags)
            if serviceId in self.announce.catalog_ser:
                files=self.persistencia.read_json()
                self.catalogo.data_media=files


if __name__ == '__main__':

    user="Javi"
    mediaId=5
    tags=["accion","Aventura","Ciencia Ficcion"]




        

