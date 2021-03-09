import scrapy
from scrapy.http.request import Request

class CTMayoristaProductDataSheetScrapy(scrapy.Spider):

    name = 'CTMayoristaProductDataSheetScrapy'

    def __init__(self, *args, **kwargs):
        self.urls = []
        product_code = kwargs.get('product_code', False)
        if product_code:
            self.urls.append(
                'https://ctonline.mx/producto/cargarFicha/'+ product_code
            )
        super(CTMayoristaProductDataSheetScrapy, self).__init__(*args, **kwargs)

    def start_requests(self):
        for url in self.urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        ct_spects = response.css('[id="ficha_tecnica"]')
        data_sheet = False
        if len(ct_spects):
            data_sheet = ""
            for ct_spect in ct_spects:
                data_sheet += ct_spect.extract()
        yield {'data_sheet': data_sheet}

