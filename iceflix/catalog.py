
import json
import sys
import random
import time
import threading
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
            print("Error al leer el fichero json\n")
            return None
    def write_json(self,data):
        try:
            with open(DATA_JSON,'w') as json_file:
                json.dump(data, json_file)
        except:
            print("Error al escribir el fichero json\n")

class MediaCatalog(IceFlix.MediaCatalog):

    def __init__(self,announcement,catalog_up_pub):
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
            if id==mediaId:
                self.providers[mediaId]=ser
                print(ser)
    def getTile(self,mediaId,userToken,current=None):
        found=False
        print(self.announcement.auth_ser)
        auth=random.choice(list(self.announcement.auth_ser.values()))
        user=""
        try:
            user = auth.whois(userToken)
        except:
            raise IceFlix.Unauthorized()
        media=IceFlix.Media()
        info=IceFlix.MediaInfo()
        self.data_media = self.persistence.read_json()
        for file in self.data_media.get("Media"):
            if str(file.get("MediaId")) == mediaId:
                found=True
                media.mediaId=str(mediaId)
                info.name=file.get("Name")
                info.tags=file.get("UserInfo").get("Tags")
        media.info=info
        if mediaId in self.providers:
            media.provider=self.providers[mediaId]
        if not found:
            raise IceFlix.WrongMediaId()
        return media
    def getTilesByName(self,name,exact,current=None):
        list_files=[]
        self.data_media = self.persistence.read_json()
        for file in self.data_media.get("Media"):
            if file.get("Name").lower() == name.lower() and exact:
                list_files.append(file.get("Name"))
            if name.lower() in file.get("Name").lower() and not exact:
                list_files.append(file.get("Name"))
        return list_files
    def getTilesByTags(self, tags, includeAllTags, userToken, current=None):
        auth=random.choice(list(self.announcement.auth_ser.values()))
        user=""
        try:
            user = auth.whois(userToken)
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
        
    def renameTile(self, mediaId, name, adminToken, current=None):
        auth=random.choice(list(self.announcement.auth_ser.values()))
        found=False
        if auth.isAdmin(adminToken):
            persistence=Persistence()
            self.data_media = persistence.read_json()
            for file in self.data_media.get("Media"):
                if str(file.get("MediaId")) == mediaId:
                    found=True
                    file["Name"]=name
                    persistence.write_json(self.data_media)
        else:
            print("Admin token incorrecto\n")
            raise IceFlix.Unauthorized()
        if not found:
            print("Media no encontrada\n")
            raise IceFlix.WrongMediaId()
        self.publiser.renameTile(mediaId,name,self.service_id)

    def addTags(self,mediaId,tags,userToken,current=None):
        found=False
        auth=random.choice(list(self.announcement.auth_ser.values()))
        user=""
        try:
            user = auth.whois(userToken)
        except:
            raise IceFlix.Unauthorized()
        self.data_media = self.persistence.read_json()
        print(user)
        for file in self.data_media.get("Media"):
            if str(file.get("MediaId")) == mediaId:
                found=True
                if user==file.get("UserInfo").get("UserName"):
                    print(user,file.get("UserInfo").get("UserName"))
                    for tag in tags:
                        if tag not in file["UserInfo"]["Tags"]:
                            file["UserInfo"]["Tags"].append(tag)
                    self.persistence.write_json(self.data_media)
        if not found:
            raise IceFlix.WrongMediaId()
        self.publiser.addTags(mediaId,user,tags,self.service_id)
        
    def removeTags(self,mediaId,tags,userToken,current=None):
        auth=random.choice(list(self.announcement.auth_ser.values()))
        found=False
        user=""
        try:
            user = auth.whois(userToken)
        except:
            raise IceFlix.Unauthorized()
        self.data_media = self.persistence.read_json()
        for file in self.data_media.get("Media"):
            if str(file.get("MediaId")) == mediaId:
                found=True
                for tag in tags:
                    if tag in file["UserInfo"]["Tags"]:
                        file["UserInfo"]["Tags"].remove(tag)
                self.persistence.write_json(self.data_media)
        if not found:
            raise IceFlix.WrongMediaId()
        self.publiser.removeTags(mediaId,user,tags,self.service_id)
    
    def getAllDeltas(self,current=None):
        print("Actualizando publicador con los datos en local\n")
        self.data_media=self.persistence.read_json()
        for file in self.data_media.get("Media"):
            mediaId=file.get("MediaId")
            nombre=file.get("Name")
            self.publiser.renameTile(str(mediaId),nombre,self.service_id)
        for file in self.data_media.get("Media"):
            mediaId=file.get("MediaId")
            user=file.get("UserInfo").get("UserName")
            tags=file.get("UserInfo").get("Tags")
            self.publiser.addTags(str(mediaId),user,tags,self.service_id)
class Announcement(IceFlix.Announcement):

    def __init__(self):
        self.catalog_ser={}
        self.catalog_valid={}
        self.auth_ser={}
        self.auth_valid={}
        self.file_ser={}
        self.file_valid={}

    def announce(self,service,serviceId,current=None):
        if service.ice_isA("::IceFlix::MediaCatalog"):
            print("[Announcement] announce Catalog: "+serviceId+"\n")
            if  serviceId not in self.catalog_ser:
                self.catalog_ser[serviceId]=IceFlix.MediaCatalogPrx.uncheckedCast(service)
                self.catalog_valid[serviceId]=time.time()
        elif service.ice_isA("::IceFlix::Authenticator"):
            print("[Announcement] announce Authenticator: "+serviceId+"\n")
            if serviceId not in self.auth_ser:
                self.auth_ser[serviceId]=IceFlix.AuthenticatorPrx.uncheckedCast(service)
                self.auth_valid[serviceId]=time.time()
        elif service.ice_isA("::IceFlix::FileService"):
            print("[Announcement] announce File: "+serviceId+"\n")
            if serviceId not in self.file_ser:
                self.file_ser[serviceId]=IceFlix.FileServicePrx.uncheckedCast(service)
                self.file_valid[serviceId]=time.time()
class FileAvailabilityAnnounce(IceFlix.FileAvailabilityAnnounce):
    def __init__(self,annoucement,catalog):
        self.announce=annoucement
        self.catalogo=catalog

    def announceFiles(self,mediaIds,serviceId,current=None):
        if serviceId in self.announce.file_ser:
            for mediaId in mediaIds:
                print("[FileAvailability] Id servicio {} Id media {}\n",serviceId,mediaId)
                services=self.announce.file_ser[mediaId]
                self.catalogo.providers_up(mediaId,services)
class CatalogUpdate(IceFlix.CatalogUpdate):
    def __init__(self,announcement,catalog):

        self.catalogo=catalog
        self.announce=announcement
        self.persistencia=Persistence()

    def renameTile(self, mediaId,  newName,  serviceId,current=None):
        if serviceId != self.catalogo.service_id:
            print("[Catalog Update] Actualizando titulo con id {} y nombre {}\n",mediaId,newName)
            if serviceId in self.announce.catalog_ser:
                files=self.persistencia.read_json()
                self.catalogo.data_media=files
            else:
                print("[Catalog Update] El servicio no esta registrado\n")

    def addTags(self, mediaId, user, tags, serviceId,current=None):
        if serviceId != self.catalogo.service_id:
            print("[Catalog Update] Actualizando tags con id {}, usuario {} y tags {}\n",mediaId,user,tags)
            if serviceId in self.announce.catalog_ser:
                files=self.persistencia.read_json()
                self.catalogo.data_media=files

    def removeTags(self, mediaId, user, tags, serviceId,current=None):
        if serviceId != self.catalogo.service_id:
            print("[Catalog Update] Eliminando tags con id {} usuario {} y tags {}\n",mediaId,user,tags)
            if serviceId in self.announce.catalog_ser:
                files=self.persistencia.read_json()
                self.catalogo.data_media=files

class Servidor(Ice.Application):

    def __init_(self):
        self.announce_ser

    def get_topic_manager(self,broker):
        key = 'IceStorm.TopicManager'
        proxy = broker.propertyToProxy(key)
        if proxy is None:
            print("property {} not set".format(key))
            return None
        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)

    def get_topic(self,topic_mgr,topic_name):
        topic=""
        try:
            topic=topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            print("Topic no valido\n")
        return topic

    def run(self,argv):
        broker=self.communicator()
        adapter=broker.createObjectAdapter("CatalogAdapter")
        adapter.activate()

        topic_mqr=self.get_topic_manager(broker)
        if not topic_mqr:
            print(topic_mqr)
            print("Invalid proxy {} \n",broker)
            return 2
        
        announce_top=self.get_topic(topic_mqr,"Announcements")
        file_top=self.get_topic(topic_mqr,"FileAvailabilityAnnounces")
        catalog_top=self.get_topic(topic_mqr,"CatalogUpdates")


        if not announce_top and not file_top and not catalog_top:
            return 2
        
        self.announce_ser=Announcement()
        publisher=catalog_top.getPublisher()
        catalog_pub=IceFlix.CatalogUpdatePrx.uncheckedCast(publisher)

        servant=MediaCatalog(self.announce_ser,catalog_pub)
        proxyCatalog=adapter.addWithUUID(servant)
        print(proxyCatalog)
        servant.service_id= proxyCatalog.ice_getIdentity().name
        print("Iniciando catalogo\n")

        catalog_up_servant=CatalogUpdate(self.announce_ser,servant)
        proxyCatalogUp=adapter.addWithUUID(catalog_up_servant)
        catalog_top.subscribeAndGetPublisher({},proxyCatalogUp)

        anno_pub= IceFlix.AnnouncementPrx.uncheckedCast(announce_top.getPublisher())
        print("Iniciando Announcement\n")

        proxyAnnounce=adapter.addWithUUID(self.announce_ser)
        announce_top.subscribeAndGetPublisher({},proxyAnnounce)

        print("Buscando anunciamientos\n")
        anno_pub.announce(proxyCatalog,servant.service_id)
        time.sleep(10)

        if len(self.announce_ser.catalog_ser)==0 :
            print("No hay anunciamientos de catalogo\n")
        else:
            print("Anunciamientos de catalogo encontrados\n")
            if len(self.announce_ser.catalog_ser)!=0:
                self.announce_ser.catalog_ser[servant.service_id].getAllDeltas()

        file_servant=FileAvailabilityAnnounce(self.announce_ser,servant)
        ProxyFile=adapter.addWithUUID(file_servant)
        file_top.subscribeAndGetPublisher({},ProxyFile)

        thread_pub=threading.Thread(target=self.announce,args=(anno_pub,proxyCatalog,servant.service_id))
        thread_ckc=threading.Thread(target=self.delete,args=())

        thread_pub.start()
        thread_ckc.start()

        broker.waitForShutdown()

        announce_top.unsubscribe(proxyAnnounce)
        file_top.unsubscribe(ProxyFile)
        catalog_top.unsubscribe(proxyCatalogUp)

    def announce(self, announce_pub,proxyCatalog,servant_id):
        while(1):
            print("Publicando anunciamientos\n")
            announce_pub.announce(proxyCatalog,servant_id)
            time.sleep(10)
    def delete(self):
        auth_array=self.announce_ser.auth_ser
        while(1):
            t=time.time()
            print("Eliminando anunciamientos de autenticador\n")
            for auth in auth_array.keys():
                if t-self.announce_ser.auth_valid[auth]>12:
                    del self.announce_ser.auth_ser[auth]
                    del self.announce_ser.auth_valid[auth]
                time.sleep(10)

            print("Eliminando anunciamientos de catalogo\n")
            for cat in self.announce_ser.catalog_ser.keys():
                if t-self.announce_ser.catalog_valid[cat]>12:
                    del self.announce_ser.catalog_ser[cat]
                    del self.announce_ser.catalog_valid[cat]
                time.sleep(10)
            print("Eliminando anunciamientos de ficheros\n")
            for fil in self.announce_ser.file_ser.keys():
                if t-self.announce_ser.file_valid[fil]>12:
                    del self.announce_ser.file_ser[fil]
                    del self.announce_ser.file_valid[fil]
                time.sleep(10)

if __name__ == '__main__':

    server=Servidor()
    sys.exit(server.main(sys.argv))



        

