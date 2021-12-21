import datetime
import hashlib
import json
import re

from geopy import Nominatim

from src.bstsouecepkg.extract import Extract
from src.bstsouecepkg.extract import GetPages


class Handler(Extract, GetPages):
    base_url = 'https://www.asiapacificex.com'
    NICK_NAME = 'asiapacificex_com'
    fields = ['overview']

    header = {
        'User-Agent':
            'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Mobile Safari/537.36',
        'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7'
    }

    def get_by_xpath(self, tree, xpath, return_list=False):
        try:
            el = tree.xpath(xpath)
        except Exception as e:
            print(e)
            return None
        if el:
            if return_list:
                return [i.strip() for i in el]
            else:
                return el[0].strip()
        else:
            return None

    def getpages(self, searchquery):
        res_list = []
        url1 = 'https://www.asiapacificex.com/?p=partner_vendor'
        url2 = 'https://www.asiapacificex.com/?p=settlement'
        tree1 = self.get_tree(url1, headers=self.header)
        tree2 = self.get_tree(url2, headers=self.header)
        names1 = self.get_by_xpath(tree1,
                                   '//span[@class="member-title"]/text()[contains(., "Name:")]/../following-sibling::span/text()',
                                   return_list=True)
        names2 = self.get_by_xpath(tree2,
                                   '//span[@class="member-title"]/text()[contains(., "Name:")]/../following-sibling::span/text()',
                                   return_list=True)
        for name in names1:
            if searchquery.lower() in name.lower():
                res_list.append(url1 + '?=' + name)
        for name in names2:
            if searchquery.lower() in name.lower():
                res_list.append(url2 + '?=' + name)
        return res_list

    def get_address(self, tree, basex):
        address = self.get_by_xpath(tree,
                                    basex + '//div/span[@class="member-title"]/text()[contains(., "Address:")]/../following-sibling::span/text()')
        try:
            zip = re.findall('\d\d\d\d\d*', address)[-1]
        except:
            zip = None
        try:
            country = address.split(' ')[-2:]
            country = ' '.join(country)
            country = re.findall('[a-zA-Z]*', country)[0]
            # geolocator = Nominatim(user_agent='anonymous@gmail.com')
            # print(geolocator.geocode(city))
        except:
            country = None

        try:
            street = address.split(zip)[0].split(',')[0]
        except:
            street = None
        temp_dict = {}
        if country and address:
            temp_dict['country'] = country
            temp_dict['fullAddress'] = address + ', ' + temp_dict['country']
        elif address:
            temp_dict['fullAddress'] = address
        if zip:
            temp_dict['zip'] = zip
        if street:
            temp_dict['streetAddress'] = street
        if temp_dict:
            return temp_dict
        else:
            return None

    def reformat_date(self, date, format):
        date = datetime.datetime.strptime(date.strip(), format).strftime('%Y-%m-%d')
        return date

    def check_create(self, tree, xpath, title, dictionary, date_format=None):
        item = self.get_by_xpath(tree, xpath)
        if item:
            if date_format:
                item = self.reformat_date(item, date_format)
            dictionary[title] = item.strip()

    def get_founders(self, tree):
        officers = []
        names = self.get_by_xpath(tree,
                                  '//div[@class="govuk-summary-list__row"]/dt[@class="govuk-summary-list__key"]/text()[contains(., "Founders")]/../../../following-sibling::div[1]//div[@class="govuk-grid-column-one-half"]/text()',
                                  return_list=True)
        incorp = self.get_by_xpath(tree,
                                   '//div[@class="govuk-summary-list__row"]/dt[@class="govuk-summary-list__key"]/text()[contains(., "Founders")]/../../../following-sibling::div[1]//div[@class="govuk-grid-column-one-quarter"]/span/text()[contains(., "From")]/../../text()',
                                   return_list=True)
        for name, icor in zip(names, incorp):
            off = {
                'name': name,
                'type': 'Individual',
                'status': 'Active',
                'occupation': 'Director',
                'officer_role': 'Director',
                'information_source': 'https://ives.minv.sk/',
                'information_provider': 'IVES',
            }
            if incorp:
                off['date_of_incorporation'] = {
                    'year': icor.split('.')[-1],
                    'month': icor.split('.')[-2],
                    'day': icor.split('.')[-3]
                }
            officers.append(off)
        return officers

    def get_comitte(self, tree):
        officers = []
        names = self.get_by_xpath(tree,
                                  '//div[@class="govuk-summary-list__row"]/dt[@class="govuk-summary-list__key"]/text()[contains(., "Members of the preparatory committee")]/../../following-sibling::div//div[@class="govuk-grid-column-one-half"]//text()[1]',
                                  return_list=True)
        borns = self.get_by_xpath(tree,
                                  '//div[@class="govuk-summary-list__row"]/dt[@class="govuk-summary-list__key"]/text()[contains(., "Members of the preparatory committee")]/../../following-sibling::div//div[@class="govuk-grid-column-one-half"]//text()[2]',
                                  return_list=True)
        names2 = self.get_by_xpath(tree,
                                   '//div[@class="govuk-summary-list__row"]/dt[@class="govuk-summary-list__key"]/text()[contains(., "Members of the preparatory committee")]/../../../following-sibling::div//div[@class="govuk-grid-column-one-half"]//text()[1]',
                                   return_list=True)
        borns2 = self.get_by_xpath(tree,
                                   '//div[@class="govuk-summary-list__row"]/dt[@class="govuk-summary-list__key"]/text()[contains(., "Members of the preparatory committee")]/../../../following-sibling::div//div[@class="govuk-grid-column-one-half"]//text()[2]',
                                   return_list=True)
        from2 = self.get_by_xpath(tree,
                                  '//div[@class="govuk-summary-list__row"]/dt[@class="govuk-summary-list__key"]/text()[contains(., "Members of the preparatory committee")]/../../../following-sibling::div//div[@class="govuk-grid-column-one-quarter"][1]/span/../text()',
                                  return_list=True)
        positions2 = self.get_by_xpath(tree,
                                       '//span[@class="govuk-grid-column-one-quarter popis"]/text()[contains(., "Position")]/../../text()',
                                       return_list=True)
        print(names2)
        print(borns2)
        print(from2)
        print(names)
        print(borns)

        if (names2 and borns2 and positions2 and from2):
            for name, born, pos, fr in zip(names2, borns2, positions2, from2):
                off = {
                    'name': name,
                    'type': 'Individual',
                    'status': 'Active',
                    'occupation': pos,
                    'officer_role': pos,
                    'information_source': 'https://ives.minv.sk/',
                    'information_provider': 'IVES',
                }
            if fr:
                off['date_of_incorporation'] = {
                    'year': fr.split('.')[-1],
                    'month': fr.split('.')[-2],
                    'day': fr.split('.')[-3]
                }
            if born:
                off['date_of_birth'] = {
                    'year': born.split('.')[-1],
                    'month': born.split('.')[-2],
                    'day': born.split('.')[-3]
                }
            officers.append(off)
        if (names and borns):
            for name, born in zip(names, borns):
                if name in names2:
                    continue
                off = {
                    'name': name,
                    'type': 'Individual',
                    'status': 'Active',
                    'occupation': 'Member of the preparatory committee',
                    'officer_role': 'Member of the preparatory committee',
                    'information_source': 'https://ives.minv.sk/',
                    'information_provider': 'IVES',
                }
                if born:
                    off['date_of_birth'] = {
                        'year': born.split('.')[-1],
                        'month': born.split('.')[-2],
                        'day': born.split('.')[-3][-2:]
                    }
                officers.append(off)

        return officers

    # def get_business_classifier(self, tree, url, basex):
    #     if url

    def get_overview(self, link_name):
        url = link_name.split('?=')[0]
        company_name = link_name.split('?=')[1]
        tree = self.get_tree(url, headers=self.header)
        company = {}

        try:
            orga_name = self.get_by_xpath(tree,
                                          f'//span[@class="member-title"]/text()[contains(., "Name:")]/../following-sibling::span/text()[contains(., "{company_name}")]')
        except:
            return None
        if orga_name: company['vcard:organization-name'] = orga_name.strip()

        baseXpath = f'//span[@class="member-title"]/text()[contains(., "Name:")]/../following-sibling::span/text()[contains(., "{company_name}")]/../../../../../..'
        company['isDomiciledIn'] = 'CN'
        logo = self.get_by_xpath(tree, baseXpath + '/div/img/@src')
        if logo:
            company['logo'] = self.base_url + '/' + logo

        company['hasActivityStatus'] = 'Active'

        self.check_create(tree,
                          baseXpath + '//div/span[@class="member-title"]/text()[contains(., "Url:")]/../following-sibling::span/a/@href',
                          'hasURL', company)

        self.check_create(tree,
                          baseXpath + '//div/span[@class="member-title"]/text()[contains(., "Email:")]/../following-sibling::span/a/@data-email',
                          'bst:email', company)

        if 'partner' in url:
            bus_class = self.get_by_xpath(tree, baseXpath + '/../../../..//h4/a/text()')
        else:
            bus_class = 'SETTLEMENT BANKS'
        if bus_class:
            company['bst:businessClassifier'] = [{
            'code': '',
            'description': bus_class,
            'label': ''
        }]

        self.check_create(tree,
                          baseXpath + '//div/span[@class="member-title"]/text()[contains(., "Tel:")]/../following-sibling::span/text()',
                          'tr-org:hasRegisteredPhoneNumber', company)



        address = self.get_address(tree, baseXpath)
        if address:
            company['mdaas:RegisteredAddress'] = address

        company['@source-id'] = self.NICK_NAME
        return company

