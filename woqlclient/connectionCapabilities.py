# connectionCapabilities.py

# const UTILS = require('./utils.js');
from .errorMessage import ErrorMessage
from .const import Const as const
from .errors import (AccessDeniedError, InvalidURIError, APIError)
from .connectionConfig import ConnectionConfig

"""
    Creates an entry in the connection registry for the server
    and all the databases that the client has access to
    maps the input authorties to a per-db array for internal storage and easy
    access control checks
    {doc:dbid => {terminus:authority =>
    [terminus:woql_select, terminus:create_document, auth3, ...]}}
"""


class ConnectionCapabilities:

    def __init__(self):
        self.connection = {}

    def _action_to_array(self, actions):
        if isinstance(actions, list) is False:
            return []
        actionList = []
        for item in actions:
            actionList.append(item['@id'])

        return actionList

    def set_capabilities(self, capabilities=None):
        self.connection = {}
        if capabilities is not None:
            self.capabilitiesKeys = capabilities.keys()
        else:
            self.capabilitiesKeys = []

        for pred in self.capabilitiesKeys:
            if (pred == 'terminus:authority') and (pred in capabilities):
                if type(capabilities[pred]) == list:
                    auths = capabilities[pred]
                else:
                    auths = [capabilities[pred]]
                for item in auths:
                    access = item['terminus:access']
                    scope = access['terminus:authority_scope']
                    actions = access['terminus:action']
                    if type(scope) != list:
                        scope = [scope]
                    if type(actions) == list:
                        action_arr = [obj['@id'] for obj in actions]
                    else:
                        action_arr = []
                    for nrec in scope:
                        if (nrec['@id'] not in self.connection):
                            self.connection[nrec['@id']] = nrec
                        self.connection[nrec['@id']]['terminus:authority'] = action_arr
            else:
                self.connection[pred] = capabilities[pred]

    def _form_resource_name(self, dbid, account):
        if(dbid == "terminus"):
            return "terminus"
        return f"{account}|{dbid}"

    def find_resource_document_id(self, dbid, account):
        testrn = self._form_resource_name(dbid, account)
        for pred in self.connection.keys():
            rec = self.connection[pred]
            if('terminus:resource_name' in rec):
                 resource_name = rec['terminus:resource_name']
                 if ('@value' in resource_name and rec['terminus:resource_name']['@value'] == testrn):
                     return pred
        return None

    def get_json_context(self):
        if "@context" in self.connection:
            ctxt = self.connection["@context"]
            ctxt['scm'] = "http://my.old.man/is/a/walrus#"
            return ctxt
        return {}

    def capabilities_permit(self, action, dbid=None, account=None):
        if (action == const.CREATE_DATABASE):
            rec = self._get_server_record()
        elif dbid is not None:
            rec = self._get_server_record(dbid, account)
        else:
            raise ValueError('no dbid provided in capabilities check ', server, dbid)
        if (rec):
            auths = rec.get('terminus:authority')
            terminusActionName = 'terminus:' + action
            if (auths and terminusActionName in auths):
                return True
        raise AccessDeniedError(
            ErrorMessage.getAccessDeniedMessage(action, dbid, account))

    def _get_server_record(self):
        """retrieves the meta-data record returned by connect for the connected server
           Returns
           =======
           {terminus:Server} JSON server record as returned by WOQLClient.connect
        """
        for obj in self.connection.values():
            if (isinstance(obj, dict) and obj.get("@type") == 'terminus:Server'):
                return obj
        return None

    def _get_db_record(self, dbid, account):
        """retrieves the meta-data record returned by connect for a particular database
           Returns
           =======
           {terminus:Database} terminus:Database JSON document as returned by WOQLClient.connect
        """
        docid = this.find_resource_document_id(dbid, account)
        if docid is not None:
            return self.connection[docid]

    def _extract_metadata(self, dbrec):
        meta = {'db': "",
            'account': "",
            'title': "",
            'description': ""}
        if ('terminus:resource_name' in dbrec) and ('@value' in dbrec['terminus:resource_name']):
            rn = dbrec['terminus:resource_name']['@value']
            if(rn == "terminus"):
                meta['db'] = rn
            elif type(rn) is str and rn:
                bits = rn.split("|")
                if(bits.length == 1):
                    meta['db'] = rn
                else:
                    meta['account'] = bits[0]
                    meta['db'] = bits[1]
        if 'rdfs:label' in dbrec:
            if type(dbrec['rdfs:label']) == list:
                label = dbrec['rdfs:label'][0]
            else:
                label = dbrec['rdfs:comment']
            if label is not None and label and '@value' in label:
                meta['description'] = label['@value']

    def _get_db_metadata(self, dbid, account):
        dbrec = self._get_db_record(dbid, account)
        if dbrec is not None:
            return self._extract_metadata(dbrec)

    def _db_capability_id(self, dbid):
        return 'doc:' + dbid

    def remove_db(self, dbid=None, srvr=None):
        """
          removes a database record from the connection registry (after deletion, for example)
          @param {String} [dbid] optional DB ID - if omitted current connection config db will be used
          @param {String} [srvr] optional server URL - if omitted current connection config server will be used
          @returns {[terminus:Database]} array of terminus:Database JSON documents as returned by WOQLClient.
        """
        docid = this.find_resource_document_id(dbid, account)
        if docid is not None:
            del self.connection['docid']
