#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Autor: ehooo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
#	UTIL CODE
## BASED ON: {{{ http://code.activestate.com/recipes/146306/ (r1)

DEBUG_MODE = False

import httplib, mimetypes, mimetools
from cStringIO import StringIO

def post_multipart(host, selector, fields, files):
	"""
	Post fields and files to an http host as multipart/form-data.
	fields is a sequence of (name, value) elements for regular form fields.
	files is a sequence of (name, filename, value) elements for data to be uploaded as files
	Return the server's response page.
	"""
	content_type, body = encode_multipart_formdata(fields, files)
	h = httplib.HTTP(host)
	h.putrequest('POST', selector)
	h.putheader('content-type', content_type)
	h.putheader('content-length', str(len(body)))
	h.endheaders()
	h.send(body)
	if DEBUG_MODE:
		print "HOST: %s"%host
		print "PATH: %s"%selector
		print "POST: %s\n"%body
	errcode, errmsg, headers = h.getreply()
	if DEBUG_MODE:
		print "RESPONSE: %s %s"%(errcode, errmsg)
		print "HEADER: %s\n"%headers
	return h.file.read()

def encode_multipart_formdata(fields, files):
	"""
	fields is a sequence of (name, value) elements for regular form fields.
	files is a sequence of (name, filename, value) elements for data to be uploaded as files
	Return (content_type, body) ready for httplib.HTTP instance
	"""

	BOUNDARY = mimetools.choose_boundary()
	CRLF = '\r\n'
	L = StringIO()
	for (key, value) in fields:
		L.write('--' + BOUNDARY)
		L.write(CRLF + 'Content-Disposition: form-data; name="%s"' % key)
		L.write(CRLF + CRLF + value + CRLF)
	for (key, filename, value) in files:
		content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
		L.write('--' + BOUNDARY)
		L.write(CRLF + 'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
		L.write(CRLF + 'Content-Type: %s' % content_type)
		L.write(CRLF + CRLF + value + CRLF)
	L.write('--' + BOUNDARY + '--' + CRLF + CRLF)
	L.seek(0)
	body = L.read()
	content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
	return content_type, body

def get_content_type(filename):
	return 
## END OF BASE OF: http://code.activestate.com/recipes/146306/ }}}
#	END UTIL CODE

import urlparse, urllib, hashlib, os, traceback
import xml.sax as sax


class SafeCreativeAPI_SAX_Parser(sax.handler.ContentHandler):
	'''
	Modo de uso:

	parse_sc = SafeCreativeAPI_SAX_Parser()
	sax.parseString(reponse, parse_sc)
	parse_sc.last = {
	  "tags"	:[]
	  "content"	:"",
	  "name"	:""
	}
	'''
	def __init__(self):
		sax.handler.ContentHandler.__init__(self)
		self.pila = []
		self.last = {"tags":[],\
					 "content":"",\
					 "name":""}

	def startElement(self, name, attrs):
		self.pila.append(self.last.copy())
		self.last = {"tags":[],\
					 "content":"",\
					 "name":""}
		self.last["name"] = name

	def endElement(self, name):
		last = self.pila.pop()
		last["tags"].append(self.last)
		self.last = last

	def characters(self, content):
		self.last["content"] += content

def parser_response(reponse):
	'''
	Throws Warning si se retorna un error en el protocolo
	Parsea la respuesta dada y retorna un objeto con la siguiente estructura:
	{"tags"	:[]
	 "content"	:"",
	 "name"	:""
	}
	'''
	global DEBUG_MODE
	if DEBUG_MODE:
		print reponse
	if not reponse.startswith("<?xml"):
		raise Warning("Wrong Response, an html format has been obtained.")
	parse_sc = SafeCreativeAPI_SAX_Parser()
	sax.parseString(reponse, parse_sc)

	id = first_content(parse_sc.last, "errorId")
	msg = first_content(parse_sc.last, "errorMessage")
	if id or msg:
		raise Warning(id, msg)

	return parse_sc.last

def first_tag(parse_res, tag):
	'''
	@parse_res Contenido retornado por "parser_response(reponse)"
	@tag String de la etiqueta a buscar

	Retorna el primer objeto con la siguiente estructura:
	{"tags"	:[]
	 "content"	:"",
	 "name"	:tag
	}
	encontrado dentro de la respuesta parseada 
	'''
	if parse_res:
		for tags in parse_res["tags"]:
			if (tags["name"] == tag):
				return tags
			else:
				if len(tags["tags"]) > 0:
					res = first_tag(tags, tag)
					if res is not None:
						return res

def first_content(parse_res, tag):
	'''
	@parse_res Contenido retornado por "parser_response(reponse)"
	@tag String de la etiqueta a buscar

	Retorna el contenido del primer objeto con etiqueta "tag" encontrado dentro de la respuesta parseada
	'''
	res = first_tag(parse_res, tag)
	if res:
		return res["content"].encode('U8','ignore')


class SafeCreativeAPI:
	API_URL = "https://api.safecreative.org/v2/"
	API_SEARCH_URL = "https://api-search.safecreative.org/v2/"
	API_SEMANTIC_URL = "https://api-search.safecreative.org/semantic-query"
	API_AUTH = "https://api.safecreative.org/api-ui/authkey.edit"

	AUTH_KEY = None #Se puede crear llamando a getAuthkey_create
	AUTH_PRIVATE_KEY = None #Se puede crear llamando a getAuthkey_create

	def __init__(self, share_key, private_key, test = False):
		self._PRIVATE_KEY = private_key
		self._SHARED_KEY = share_key

		global DEBUG_MODE
		DEBUG_MODE = test
		if DEBUG_MODE:
			self.API_URL = "https://arena.safecreative.org/v2/"
			self.API_SEARCH_URL = "https://arena.safecreative.org/v2/"
			self.API_SEMANTIC_URL = "https://arena.safecreative.org/semantic-query"
			self.API_AUTH = "https://arena.safecreative.org/api-ui/authkey.edit"

	def readInfo(self, params, sign=None, url=None, debug=False):
		'''
		Thanks to Manuel Polo (mistermx at gmail dot com) for UTF-8 support

		@params Parametros a enviar
		@sign Firma con la que realizar la "signature"
		@url Url donde hacer la conexion, por defecto "self.API_URL"
		@return El contenido de la peticion

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo.
			Si la peticion no ha retornado 200, el primer parametro es la respuesta y el segundo la cabecera
		'''
		global DEBUG_MODE
		if DEBUG_MODE:
			print "Procesando parametros" + str(params)
		encoded = [(k, self.toUTF8(v)) for k, v in params.items()]
		if DEBUG_MODE:
			print "encoded:"+str(encoded)
		post = urllib.urlencode(encoded)
		if DEBUG_MODE:
			print "encoded:"+post
		if sign:
			unencoded = '&'.join([ (k + '=' + self.toUTF8(v)) for k,v in sorted(params.items())])
			if DEBUG_MODE:
				print "unencoded: " + unencoded
			sha1 = hashlib.sha1()
			sha1.update(sign + "&")
			sha1.update(unencoded)
			signature=sha1.hexdigest()
			if DEBUG_MODE:
				print "signature="+signature
			post += "&signature="+signature

		if url is None:
			url = self.API_URL

		if DEBUG_MODE and debug:#http://wiki.safecreative.net/wiki/Signature_troubleshooting
			post += "&debug-component=signature.analysis"

		if DEBUG_MODE:
			print "Conectando con: "+url+"?"+post

		#Usamos POST para mandar los datos cifrados
		parseUrl = urlparse.urlparse(url);
		host = parseUrl.netloc
		if parseUrl.port:
			host += ":"+parseUrl.port
		conn = httplib.HTTPConnection(host);
		headers = {"Content-type": "application/x-www-form-urlencoded;charset=UTF-8", "Accept": "*/*", "UserAgent":"ehooo's SafeCreative Python API"}
		conn.request("POST",parseUrl.path, post, headers)
		response = conn.getresponse()
		if response.status != httplib.OK:
			if DEBUG_MODE:
				print "Response:", response.status
			ret = response.getheaders()
			conn.close()
			raise Warning(response.status, ret)
			return ret
		ret = response.read()
		conn.close()
		return parser_response(ret)

	def toUTF8(self,s):
		"""Convert unicode to utf-8."""
		if isinstance(s, unicode):
			return s.encode("utf-8")
		else:
			return unicode(str(s),"utf-8").encode("utf-8")

	#Authorization and validation
	def getVersion(self):
		'''
		http://wiki.safecreative.net/wiki/Version

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		return first_content(self.readInfo({"component":"version"}), "version")

	def getZtime(self):
		'''
		http://wiki.safecreative.net/wiki/Ztime

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		return first_content(self.readInfo({"component":"ztime"}), "ztime")

	def getAuthkey_create(self):
		'''
		Inserta el valor de authkey y privatekey y retorna el contenido parseado
		http://wiki.safecreative.net/wiki/Authkey.create

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "authkey.create",\
				 "ztime":self.getZtime(),\
				 "sharedkey":self._SHARED_KEY}
		param = self.readInfo(param, self._PRIVATE_KEY)
		self.AUTH_KEY = first_content(param, "authkey")
		self.AUTH_PRIVATE_KEY = first_content(param, "privatekey")
		return param

	def getAuthkey_state(self):
		'''
		http://wiki.safecreative.net/wiki/Authkey.state

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "authkey.state",\
				 "ztime":self.getZtime(),\
				 "sharedkey":self._SHARED_KEY,\
				 "authkey":self.AUTH_KEY}
		return self.readInfo(param, self._PRIVATE_KEY)

	#Master tables
	def getUser_licenses(self, page=1, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/User.licenses

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "user.licenses",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "page":page,\
				 "locale":locale}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	def getLicense_features(self, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/License.features

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "license.features",\
				 "locale":locale}
		return self.readInfo(param)

	def getUser_countries(self, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/User.countries

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "user.countries",\
				 "locale":locale}
		return self.readInfo(param)

	def getUser_profiles(self):
		'''
		http://wiki.safecreative.net/wiki/User.profiles

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "user.profiles",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	def getWork_types(self, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/Work.types

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.types",\
				 "locale":locale}
		return self.readInfo(param)

	def getWork_types_tree(self, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/Work.types.tree

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.types.tree",\
				 "locale":locale}
		return self.readInfo(param)

	def getWork_languages(self, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/Work.languages

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.languages",\
				 "locale":locale}
		return self.readInfo(param)

	#Works info
	def getWork(self, code, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/Work.get

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.get",\
				 "code":code,\
				 "locale":locale}
		return self.readInfo(param)

	def getWork_private(self, code, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/Work.get.private

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.get.private",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "code":code,\
				 "locale":locale}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	def getWork_list(self, page=1, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/Work.list

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.list",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "page":page,\
				 "locale":locale}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	def getWork_certificate(self, code, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/Work.certificate

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.certificate",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "code":code,\
				 "locale":locale}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	def getWork_download_private(self, code):
		'''
		http://wiki.safecreative.net/wiki/Work.download.private

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.download.private",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "code":code}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	#Works management
	def upload_lookup(self, upload_filename):
		'''
		http://wiki.safecreative.net/wiki/Work.upload.lookup

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.upload.lookup",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "filename":upload_filename}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	def upload_begin(self, uploadid, uploadurl):
		'''
		http://wiki.safecreative.net/wiki/Work.upload.begin

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.upload.begin",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "uploadid":uploadid}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY, uploadurl)

	def upload_chunk(self, uploadid, uploadurl, offset, data):
		'''
		http://wiki.safecreative.net/wiki/Work.upload.chunk

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.upload.chunk",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "uploadid":uploadid,\
				 "offset":offset,\
				 "data":data}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY, uploadurl)

	def upload_commit(self, uploadid, uploadurl, length, checksum):
		'''
		http://wiki.safecreative.net/wiki/Work.upload.commit

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.upload.commit",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "uploadid":uploadid,\
				 "length":length,\
				 "checksum":checksum}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY, uploadurl)

	def upload_raw(self, raw_file, filename):
		'''
		http://wiki.safecreative.net/wiki/API_upload_servlet

		Return 'uploadticket' o None si el fichero no existe

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		response = self.upload_lookup(os.path.basename(filename))
		selector = first_content(response, 'uploadurl')
		selector += "/api-upload"
		#selector = "http://upload01.safecreative.org/api-upload"
		parseUrl = urlparse.urlparse(selector);
		host = parseUrl.netloc
		if parseUrl.hostname:
			host = parseUrl.hostname
		if parseUrl.port:
			host += ":"+parseUrl.port
		fields = [("uploadid", first_content(response, 'uploadid'))]
		files = [("file", os.path.basename(filename), raw_file)]
		return post_multipart(host, selector, fields, files)

	def upload_file(self, filename):
		'''
		Helper for 'upload_raw(raw_file, filename)'
		if uploader have error, try to upload with 'upload_raw_chunk(raw_file, filename)'
		'''
		ret = None
		if os.path.isfile(filename):
			ret = self.upload_raw(open(filename, "rb").read(), filename)
		return ret

	def work_register(self, noncekey, values={}):
		'''
		@noncekey Se obtiene desde getAuthkey_state()
		http://wiki.safecreative.net/wiki/Work.register

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		Throws ValueError si una de las claves de "values" no esta soportada
		'''
		param = {"component": "work.register",\
				"ztime":self.getZtime(),\
				"authkey":self.AUTH_KEY ,\
				"noncekey":noncekey }

		claves_soportadas = ["code","title","profile","excerpt","license","worktype","language","tags","extratags",\
				"allowdownload","registrypublic","usealias","alias","userauthor","userrights","final","obs","meta"\
				"editlocked","versionof","derivationof","compositionof","text","filename", "uploadticket", "url",\
				"checksum", "size"]

		for key in values:
			if key in claves_soportadas:
				param[key] = values[key]
			elif key.startswith("link") or key.startswith("extralink"):
				param[key] = values[key]
			else:
				raise ValueError("'"+key+"' tag it's not supported")

		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	def work_attachfile(self, uploadticket, title, workcode, public=None):
		'''
		http://wiki.safecreative.net/wiki/Work.attachfile

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.attachfile",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "title":title,\
				 "uploadticket":uploadticket,\
				 "workcode":workcode}
		if public:
			param['public'] = public
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	def work_delete(self, code):
		'''
		http://wiki.safecreative.net/wiki/Work.delete

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.delete",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "code":code}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	#Multiauthorship
	def getWork_rightsholders_add(self, workcode, mail, roles, canedit, private=None):
		'''
		http://wiki.safecreative.net/wiki/Work.rightsholders.add

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.rightsholders.add",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "workcode":workcode,\
				 "mail":mail,\
				 "roles":roles,\
				 "canedit":canedit}
		if private:
			param['private'] = private
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	def getWork_rightsholders_list(self, workcode):
		'''
		http://wiki.safecreative.net/wiki/Work.rightsholders.list

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.rightsholders.list",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "workcode":workcode}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	def getWork_rightsholders_remove(self, workcode, usercode):
		'''
		http://wiki.safecreative.net/wiki/Work.rightsholders.remove

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "work.rightsholders.remove",\
				 "ztime":self.getZtime(),\
				 "authkey":self.AUTH_KEY,\
				 "workcode":workcode,\
				 "usercode":usercode}
		return self.readInfo(param, self.AUTH_PRIVATE_KEY)

	#Search
	def search_by_query(self, query, page=1, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/Search.byquery

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "search.byquery",\
				 "query":query,\
				 "page":page,\
				 "locale":locale}
		return self.readInfo(param, url=self.API_SEARCH_URL)

	def search_by_fields(self, values={}, page=1, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/Search.byfields

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		Throws ValueError si una de las claves de "values" no esta soportada
		'''
		param = {"component": "search.byfields",\
				 "page":page,\
				 "locale":locale}

		claves_soportadas = ["code","name","excerpt","user.name","user.code","allowDownload","allowRightsRequests",
							 "tag","license.code","license.name","license.shortName",\
							 "workType.code","workType.name","workTypeGroup.code","workTypeGroup.name"]

		i = 0
		for field in values:
			i += 1
			if field in claves_soportadas:
				param['field'+str(i)] = field
				param['value'+str(i)] = values[field]
			else:
				raise ValueError("'"+field+"' tag it's not supported")
		return self.readInfo(param, url=self.API_SEARCH_URL)

	def search_by_hash(self, md5=None, sha1=None, user=None, page=1, locale="es"):
		'''
		http://wiki.safecreative.net/wiki/Search.byhash

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		'''
		param = {"component": "search.byhash ",\
				 "page":page,\
				 "locale":locale}
		if md5:
			param['md5'] = md5
		if sha1:
			param['sha1'] = sha1
		if user:
			param['user'] = user
		return self.readInfo(param)

	#Semantic services
	def semantic_query(self, key, value):
		'''
		http://wiki.safecreative.net/wiki/Semantic.query

		Throws IOError si falla la conexion
		Throws SAXParseException si falla el parser
		Throws Warning si se retorna un error en el protocolo
		Throws ValueError si una de las claves de "values" no esta soportada
		'''
		claves_soportadas = ["adler32","crc32","ed2kfileid","md2","md4","md5","sha","sha1","sha384","sha512","size",\
				 "part32k.first","part32k.last","part32k.middle",\
				 "torrent.32768","torrent.49152","torrent.65536","torrent.98304",\
				 "torrent.131072","torrent.196608","torrent.262144","torrent.393216",\
				 "torrent.524288","torrent.786432","torrent.1048576","torrent.1572864",\
				 "torrent.2097152","torrent.3145728","torrent.4194304"]
		if not key in claves_soportadas:
			raise ValueError("'"+key+"' tag it's not supported")
		return self.readInfo({key:value}, url=self.API_SEMANTIC_URL)

	def getAuthorization_Url(self, level):
		'''
		http://wiki.safecreative.net/wiki/User_authorization
		Retorna la url donde autenticar al usuario
		'''
		claves_soportadas = ["GET","ADD","MANAGE"]
		if not level in claves_soportadas:
			raise ValueError("'"+level+"' it's not supported level")

		param = {"authkey":self.AUTH_KEY,\
				"level":level,\
				"sharedkey":self._SHARED_KEY,\
				"ztime":self.getZtime()}
		post = urllib.urlencode(param)
		post += "&signature="+hashlib.sha1(self.AUTH_PRIVATE_KEY+"&"+post).hexdigest()
		return self.API_AUTH+"?"+post


