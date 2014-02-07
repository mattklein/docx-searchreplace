import logging
import re
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def start(request):
    if request.method == 'GET':
        request.session.flush()
        return render_to_response('docx_search_replace/start.html')

    elif request.method == 'POST':
        uploaded_file = request.FILES['file_']
        stored_file = tempfile.NamedTemporaryFile(delete=False)
        stored_file.write(uploaded_file.read())
        # The filename of the file stored on the server's filesystem
        request.session['stored_archive_filename'] = stored_file.name
        # The filename of the "upload" -- i.e., the filename of the file on the user's filesystem
        request.session['uploaded_filename'] = uploaded_file.name
        return HttpResponseRedirect('/docx_search_replace/configure_search_replace')

    else:
        return HttpResponseBadRequest('Invalid method: %s' % request.method)


@csrf_exempt
def configure_search_replace(request):
    if request.method == 'GET':
        zf_in = ZipFile(request.session['stored_archive_filename'], mode='r')
        all_filenames_lst = zf_in.namelist()
        all_filenames = set(all_filenames_lst)
        assert len(all_filenames) == len(all_filenames_lst), "Duplicate filenames in the input file?!"
        zf_in.close()
        return render_to_response('docx_search_replace/configure_search_replace.html',
                                  {'filenames': sorted(all_filenames)})
    elif request.method == 'POST':
        replacements = []
        for i in range(1, 6):  # We have input fields "from1", "to1"... "from5", "to5"
            if request.POST['from%d' % i]:
                replacements.append((request.POST['from%d' % i], request.POST['to%d' % i]))
        logging.info('replacements: %s' % replacements)

        selected_filenames = [k for k in request.POST if request.POST[k] == 'on']
        logging.info('selected_filenames: %s' % selected_filenames)

        zf_in = ZipFile(request.session['stored_archive_filename'], mode='r')
        all_filenames = zf_in.namelist()
        stored_output_file = tempfile.NamedTemporaryFile(delete=False)
        zf_out = ZipFile(stored_output_file.name, mode='w', compression=zf_in.compression)

        for fname in selected_filenames:
            file_contents = zf_in.open(fname).read().decode('utf-8')
            for r in replacements:
                file_contents = file_contents.replace(*r)
            zf_out.writestr(fname, file_contents.encode('utf-8'))

        filenames_to_copy_unchanged = set(all_filenames) - set(selected_filenames)
        for fname in filenames_to_copy_unchanged:
            zf_out.writestr(fname, zf_in.open(fname).read(), compress_type=ZIP_DEFLATED)

        zf_in.close()
        zf_out.close()

        orig_uploaded_filename = request.session['uploaded_filename']
        if orig_uploaded_filename.endswith('.docx'):
            downloading_filename = re.sub('.docx$', '_EDITED.docx', orig_uploaded_filename)
        else:
            downloading_filename = orig_uploaded_filename + '_EDITED'

        ret_file = open(stored_output_file.name, 'rb')
        resp = HttpResponse(status=200,
                content=ret_file.read(),
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        resp['Content-Disposition'] = 'attachment; filename="%s"' % downloading_filename
        return resp

    else:
        return HttpResponseBadRequest('Invalid method: %s' % request.method)
