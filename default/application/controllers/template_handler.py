__author__ = 'cage'

import logging

from application.controllers.basehandler import UserHandler

from google.appengine.ext.webapp.util import login_required
from google.appengine.ext import ndb

from application import blob_files

PICKLED_TASKOBJ = 'gmailtask'
GCS_UPLOAD_FOLDER = '/upload'
BUCKET = 'ddim-mail-1'


class TemplateManageHandler(UserHandler):
    @login_required
    def get(self):


        delete_tempalte = self.request.get('delete_template')
        if delete_tempalte:
            data_template = ndb.Key(urlsafe=delete_tempalte).get()
            if data_template:
                data_template.key.delete()

                return self.redirect('/template')

        params = {}

        ancestor_key = ndb.Key('User', self.user.email())
        user_templates = blob_files.BlobFiles.query_template(ancestor_key).fetch()

        params.update(dict(templates=user_templates))

        self.render('template.html', **params)


    def post(self):

        context = dict(failed='No file data', use_blobstore=False)

        # read upload data, save it in GCS and a zip archive
        file_data = self.request.get("file", default_value=None)
        if file_data:

            filename = self.request.POST["file"].filename
            ancestor_key = ndb.Key('User', self.user.email())
            bf = blob_files.BlobFiles.new(filename, bucket=BUCKET, folder=GCS_UPLOAD_FOLDER,
                                          ancestor_key=ancestor_key)
            if bf:
                bf.blob_write(file_data)
                # bf.put_async()
                bf.put()

                logging.info('Uploaded and saved in default GCS bucket : ' + bf.gcs_filename)

                # update zip archive. make sure this (new) bf will be archived
                # bzf = blob_files.blob_archive(new_bf=bf)

                # context.update(dict(failed=None, bzf_url=bzf.serving_url, bzf_name=bzf.filename,
                # bf_url=bf.serving_url, bf_name=bf.filename))
                context.update(dict(failed=None, bf_url=bf.serving_url, bf_name=bf.filename))
            else:
                context.update(
                    dict(failed='Overwrite blocked. The GCS file already exists in another bucket and/or folder'))
        else:
            logging.warning('No file data')

        return self.redirect('/template')

        # self.render_template('template.html', **context)