# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from ..items import ProjetlogicItem

class LogicImmoSpider(scrapy.Spider):
    name = 'logic_immo'
    allowed_domains = ['logic-immo.com']
    start_urls = ['http://www.logic-immo.com/index-villes-vente.html']
    #Parse la page d'index pour avoir les villes affichées 
    def parse(self, response):
        all_links =[response.urljoin(url) for url in response.css(".logicgrey::attr(href)").extract()]
        for link in all_links:
            yield Request(link,callback=self.parse_cities)
            
    #Parse la première page d'annonce de la ville 
    def parse_cities(self, response):
        #Puisqu'il existe des offres ORPI structurées d'une manière différente, on traite les deux cas ici :
        all_links_cities = [response.urljoin(url) for url in response.css(".offer-link::attr(href)").extract()]
        liste_orpi = [response.urljoin(url) for url in response.css(".offer-link::attr(data-orpi)").extract()]
        all_links_cities.extend(liste_orpi)
        all_links_cities = self.clean_orpi(all_links_cities)
        for link in all_links_cities :
            yield Request(link,callback=self.parse_annonce)
            
    #Parse les données nécessaires pour insérer dans MongoDB
    def parse_annonce(self, response):
        url = response.request.url #On récupère l'url
        dict_tit = self.title_split(response.css('title::text').extract_first()) #On sépare le titre et le prix
        name2 = dict_tit['title'] #On attribue le titre
        desc=response.css('.offer-description-text h2::text').extract_first() + response.css('.offer-description-text p::text').extract_first()
        #Pour la description, elle débute dans une balise h2 puis finit dans une balise p, on les rajoute donc ensemble
        location = self.clean_spaces(response.css('.offer-block-lastrow p::text').extract_first()) #On obtient la location du bien
        typ = self.clean_spaces(response.css('.col-xs-3.offer-type p::text').extract_first())  #On obtient le type du bien
        pr = dict_tit['prix'] #On attribue le prix
        yield ProjetlogicItem(url=url,              #On crée l'Item qu'on va faire passer dans la pipeline, directement dans la base MongoDB
                              location=location,
                              name=name2,
                              desc=desc,
                              typ=typ,
                              pr=pr)
    
    #Retire les espaces superflus
    def clean_spaces(self, string_):
        if string_ is not None:
            return " ".join(string_.split())
    
    #Dans parse_cities, en récupérant un lien d'une annonce ORPI,
    #on a le lien du site au lieu de l'annonce. On utilise clean_orpi pour la retirer de la liste
    def clean_orpi(self,liste):
        orpi = "http://www.orpi.com"
        liste= [x for x in liste if x != orpi]
        return liste
    
    #Dans la balise titre de la page html d'une annonce, on a son titre suivi de son prix :
    # on exploite alors ces 2 données en les séparants
    def title_split(self,string):
        title,prix = string.split(',')
        prix,c = prix.split('€')
        return {'title':title,'prix':prix}