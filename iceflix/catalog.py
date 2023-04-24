
import json
import logging
import Ice
import IceStorm

Ice.loadSlice("iceflix.ice")
import Iceflix

DATA_JSON = "data/data.json"


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

class MediaCatalog(Iceflix.MediaCatalog):

    def __init__(self, auth_service):
        self.auth_service = auth_service

    def getTile(self, mediaId, userToken, current=None):

        user=""
        try:
            user = self.auth_service.whois(userToken)
        except:
            raise Iceflix.Unauthorized()
        
        media=Iceflix.Media()
        info=Iceflix.MediaInfo()
        persistence=Persistence()
        media_catalog = persistence.read_json()

        for file in media_catalog.get("Media"):
            if file.get("MediaId") == mediaId:
                media.mediaId=mediaId
                info.name=file.get("Name")
                for tags in media_catalog.get("Tags"):
                    info.tags=tags
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
            raise Iceflix.Unauthorized()
        
        list_files=[]
        persistence=Persistence()
        media_catalog = persistence.read_json()
        for file in media_catalog.get("Media"):
            for tag in tags:
                if includeAllTags:
                    for tag_file in file.get("Tags"):
                        if tag == tag_file:
                            list_files.append(file.get("Name"))
                else:
                    for tag_file in file.get("Tags"):
                        if tag in tag_file:
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
            raise Iceflix.Unauthorized()
        
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
            raise Iceflix.Unauthorized()
        
        persistence=Persistence()
        media_catalog = persistence.read_json()
        for file in media_catalog.get("Media"):
            if file.get("MediaId") == mediaId:
                for tag in tags:
                    file["Tags"].remove(tag)
                persistence.write_json(media_catalog)
        return 0
    
