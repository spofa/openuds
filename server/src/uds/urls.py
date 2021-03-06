# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Virtual Cable S.L.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#    * Neither the name of Virtual Cable S.L. nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
@author: Adolfo Gómez, dkmaster at dkmon dot com
'''

from django.conf.urls import include, url
from uds.core.util.modfinder import loadModulesUrls
from uds import REST
import uds.web.views;

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('uds',),
}

urlpatterns = [
    url(r'^$', uds.web.views.index, name='uds.web.views.index'),
    url(r'^login/$', uds.web.views.login, name='uds.web.views.login'),
    url(r'^login/(?P<tag>.+)$', uds.web.views.login, name='uds.web.views.login'),
    url(r'^logout$', uds.web.views.logout, name='uds.web.views.logout'),
    # Icons
    url(r'^transicon/(?P<idTrans>.+)$', uds.web.views.transportIcon, name='uds.web.views.transportIcon'),
    # Images
    url(r'^srvimg/(?P<idImage>.+)$', uds.web.views.serviceImage, name='uds.web.views.serviceImage'),
    url(r'^galimg/(?P<idImage>.+)$', uds.web.views.image, name='galleryImage'),
    # Error URL
    url(r'^error/(?P<idError>.+)$', uds.web.views.error, name='uds.web.views.error'),
    # Transport own link processor
    url(r'^trans/(?P<idService>.+)/(?P<idTransport>.+)$', uds.web.views.transportOwnLink, name='TransportOwnLink'),
    # Authenticators custom html
    url(r'^customAuth/(?P<idAuth>.*)$', uds.web.views.customAuth, name='uds.web.views.customAuth'),
    # Preferences
    url(r'^prefs$', uds.web.views.prefs, name='uds.web.views.prefs'),
    # Change Language
    url(r'^i18n/', include('django.conf.urls.i18n')),
    # Downloads
    url(r'^idown/(?P<idDownload>[a-zA-Z0-9-]*)$', uds.web.views.download, name='uds.web.views.download'),
    # downloads for client
    url(r'^down$', uds.web.views.client_downloads, name='uds.web.views.client_downloads'),
    url(r'^down/(?P<os>[a-zA-Z0-9-]*)$', uds.web.views.client_downloads, name='uds.web.views.client_downloads'),
    url(r'^pluginDetection/(?P<detection>[a-zA-Z0-9-]*)$', uds.web.views.plugin_detection, name='PluginDetection'),
    # Client access enabler
    url(r'^enable/(?P<idService>.+)/(?P<idTransport>.+)$', uds.web.views.clientEnabler, name='ClientAccessEnabler'),

    # Custom authentication callback
    url(r'^auth/(?P<authName>.+)', uds.web.views.authCallback, name='uds.web.views.authCallback'),
    url(r'^authinfo/(?P<authName>.+)', uds.web.views.authInfo, name='uds.web.views.authInfo'),
    url(r'^about', uds.web.views.about, name='uds.web.views.about'),
    # Ticket authentication
    url(r'^tkauth/(?P<ticketId>.+)$', uds.web.views.ticketAuth, name='TicketAuth'),

    # REST Api
    url(r'^rest/(?P<arguments>.*)$', REST.Dispatcher.as_view(), name="REST"),

    # Web admin GUI
    url(r'^adm/', include('uds.admin.urls')),

    # Files
    url(r'^files/(?P<uuid>.+)', uds.web.views.file_storage, name='uds.web.views.file_storage'),

    # Internacionalization in javascript
    # Javascript catalog
    url(r'^jsi18n/(?P<lang>[a-z]*)$', uds.web.views.jsCatalog, js_info_dict, name='uds.web.views.jsCatalog'),
]

# Append urls from special dispatchers
urlpatterns += loadModulesUrls()
