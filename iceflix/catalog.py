
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

    def __init__(self, auth_service):
        self.auth_service = auth_service

    def getTile(self, mediaId, userToken, current=None):

        user=""
        try:
            user = self.auth_service.whois(userToken)
        except:
            raise IceFlix.Unauthorized()
        
        media=IceFlix.Media()
        info=IceFlix.MediaInfo()
        persistence=Persistence()
        media_catalog = persistence.read_json()

        for file in media_catalog.get("Media"):
            if file.get("MediaId") == mediaId:
                media.mediaId=str(mediaId)
                info.name=file.get("Name")
                info.tags=file.get("UserInfo").get("Tags")
        media.info=info
        return media


    def getTilesByName(self, name, exact, current=None):
        
        list_files=[]
        persistence=Persistence()
        media_catalog = persistence.read_json()

        for file in media_catalog.get("Media"):
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
        for i in range(len(tags)):
            tags[i] = tags[i].lower()
        tagsarray=[]
        persistence=Persistence()
        media_catalog = persistence.read_json()
        for file in media_catalog.get("Media"):
            userinfo=file.get("UserInfo")
            if userinfo.get("UserName") == user:
                if includeAllTags:
                    for tag in userinfo.get("Tags"):
                        tagsarray.append(tag.lower())

                        for tagssearch in tags:
                            if tagssearch in tagsarray:
                                tags.remove(tagssearch)
                    if len(tags)==0:
                        list_files.append(file.get("Name"))
                else:
                    for tag in userinfo.get("Tags"):
                        for tagssearch in tags:
                            if tagssearch in tag:
                                list_files.append(file.get("Name"))
        return list_files
        
    def newMedia(self, mediaId, provider, current=None):

        persistence=Persistence()
        media_catalog = persistence.read_json()
        new_media={"MediaId":mediaId,"Name":mediaId,"Tags":[]}
        media_catalog["Media"].append(new_media)
        persistence.write_json(media_catalog)
        return 0
        
    def removeMedia(self, mediaId, provider, current=None):
        persistence=Persistence()
        media_catalog = persistence.read_json()
        for file in media_catalog.get("Media"):
            if file.get("MediaId") == mediaId:
                media_catalog["Media"].remove(file)
                persistence.write_json(media_catalog)
        return 0
    def renameTile(self, mediaId, name, adminToken, current=None):

        if self.auth_service.isAdmin(adminToken):
            persistence=Persistence()
            media_catalog = persistence.read_json()
            for file in media_catalog.get("Media"):
                if file.get("MediaId") == mediaId:
                    file["Name"]=name
                    persistence.write_json(media_catalog)
        else:
            logging.info("Admin token incorrecto")
        
        return 0

    def addTags(self, mediaId, tags, userToken, current=None):

        user=""
        try:
            user = self.auth_service.whois(userToken)
        except:
            raise IceFlix.Unauthorized()
        
        persistence=Persistence()
        media_catalog = persistence.read_json()
        for file in media_catalog.get("Media"):
            if file.get("MediaId") == mediaId:
                for tag in tags:
                    file["Tags"].append(tag)
                persistence.write_json(media_catalog)
        return 0
        
    def removeTags(self, mediaId, tags, userToken, current=None):
        
        user=""
        try:
            user = self.auth_service.whois(userToken)
        except:
            raise IceFlix.Unauthorized()
        
        persistence=Persistence()
        media_catalog = persistence.read_json()
        for file in media_catalog.get("Media"):
            if file.get("MediaId") == mediaId:
                for tag in tags:
                    file["Tags"].remove(tag)
                persistence.write_json(media_catalog)
        return 0
    
    


if __name__ == '__main__':

    #main para pruebas
    i=0

        

