import codecs
import sys
import warcat.model

prefix = sys.argv[1]

warc_filename = (prefix + '.warc.gz')
records_filename = (prefix + '.records')
records = []
warc = warcat.model.WARC()

warc.load(warc_filename)
for record in warc.records:
    if record.header.fields['warc-type'] == 'resource' \
          and record.header.fields['warc-target-uri'].startswith('ftp://'):
        records.append(';'.join([
            record.header.fields['warc-block-digest'],
            record.header.fields['warc-record-id'],
            record.header.fields['warc-date'],
            record.header.fields['warc-target-uri']]))

with codecs.open(records_filename, 'w', encoding='utf8') as f:
    f.write('\n'.join(records))
