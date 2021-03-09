import scrapy 
from scrapy.http.request import Request
import re

class CTMayoristaProductFeaturesScrapy(scrapy.Spider):

    name = 'CTMayoristaProductFeaturesScrapy'

    def __init__(self, *args, **kwargs):

        self.urls = [ ]
        path =  kwargs.get('path',False)
        if path:
            self.urls.append(
                'https://ctonline.mx/'+path
            )
        super(CTMayoristaProductFeaturesScrapy, self).__init__(*args, **kwargs)

    def start_requests(self):
        for url in self.urls:
            yield  Request(url, callback=self.parse)

    def parse(self, response):
        images = []
        #ct_thumbnails_principales = response.css('[id="thumbnails_principales"]')        
        #if len(ct_thumbnails_principales):
        #    for ct_thumbnails in ct_thumbnails_principales:
        #        for thumbnails in ct_thumbnails.css('.itm-border'):
        #            for thumbnail in thumbnails.css('::attr(style)').extract():
        #                url_thumbnail = re.search("(?P<url>https?://[^\s]+)", thumbnail).group("url")[:-2]
        #                images.append(url_thumbnail)
        ct_images = response.css('[id="img-producto"]')
        if len(ct_images):
            for ct_image in ct_images:
                image_url = ct_image.css('.img-responsive ::attr(src)')
                if len(image_url):
                    for image in image_url:
                        images.append(image.extract())

        features = False
        ct_features = response.css('[id="ct_features"]')
        if len(ct_features):
            for ct_feature in ct_features:                
                features = ct_feature.extract()
        yield {'images': images, 'features':features}