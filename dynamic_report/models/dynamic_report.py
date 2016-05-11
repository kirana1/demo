from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import StringIO
import base64
import csv

from textwrap import dedent


class dynamic_xls_report(osv.TransientModel):
    _name = 'dynamic.xls.report'
    
    _columns = {
                'report_name':fields.char('Report Name'),
                'model_name': fields.many2one('ir.model','Model',help="Select the model name."),
                'field_name':fields.many2many('ir.model.fields','rel_fields_model_rpt','wiz_id','rec_id','Field Name', help="Select the required fields."),
                'search_domain':fields.char('Domain'),
                'm2m_value' : fields.boolean('Value', help='Select if You want the value instead of id for Many2one field'),
                'filedata': fields.binary('File', readonly=True),
                'filename': fields.char('Filename', size = 64, readonly=True),
                'limit_rec': fields.integer('Limit', help="Limit your records", name="Record Limit"),
                'order_type':fields.boolean('Order',help='Check if you want the records in descending order'),
                'order_on_field' : fields.many2one('ir.model.fields','Order BY',domain="[('model_id','=',model_name)]",help="Select the field by which you want to sort."),
                'set_offset': fields.integer('Offset'),
                'domain_lines': fields.one2many('dynamic.domain.line','dynamic_rpt_id', 'Domain',help="Put the domain if any"),
                
                }
    
    def create_menu(self,cr, uid, view_id, context):
        print '-------------create_tree_view-----------------'
        print cr,uid,view_id,'-------------cr,uid,view_id--------------'
        return {
                'type': 'ir.actions.act_window',
                'name': 'Employee',
                'view_mode': 'tree',
                'view_id': view_id,
                'res_model': 'dynamic.xls.report',
                'context': context,
                'target':'new',
             }
    
#    def print_quotation(self, cr, uid, ids, context=None):
#        '''
#        This function prints the request for quotation and mark it as sent, so that we can see more easily the next step of the workflow
#        '''
#        assert len(ids) == 1, 'This option should only be used for a single id at a time'
#        self.signal_workflow(cr, uid, ids, 'send_rfq')
#        return self.pool['report'].get_action(cr, uid, ids, 'purchase.report_purchasequotation', context=context)
    
    def create(self, cr, uid, vals, context=None):
        print '-------------call create method----------- '
        print cr, uid, vals, context,'-----------------cr, uid, vals, context'
        field_vals = []
        res = super(dynamic_xls_report, self).create(cr, uid, vals, context=context)
        print res,'----------------res'
        record_obj = self.browse(cr, uid,res)
        field_names = record_obj.field_name 
        model_name = record_obj.model_name.model
        menu_name = record_obj.report_name
        print field_names,model_name, '----------------------field_names --model_name-----------'
        emp_obj = self.pool.get(model_name)
        emp_record = emp_obj.search(cr, uid, [])
        print emp_record,'----------------emp_record -----------------'
        field_vals = {
                      'name':menu_name,
                      'parent_menu': 'dynamic_report.menu_wizard_dynamic_xls_report',
                      }
        print field_vals,'-------------field_vals----------------'
        for rec in emp_record:
            gender = emp_obj.browse(cr, uid, rec).gender
            work_email = emp_obj.browse(cr, uid, rec).work_email
            print gender,work_email,'----------------------gender-------work_email'
        menu_obj = self.pool.get('ir.ui.menu')
        parent_menu_ids = menu_obj.search(cr, uid, [('name','=','Dynamic Reports')])
        for parent_menu_id in parent_menu_ids:
            parent_menu_id = menu_obj.browse(cr, uid,parent_menu_id).parent_id
#        menu_id = menu_obj.create(cr, uid, field_vals)
        print parent_menu_id,'------------------parent_view_id'
#------------------------------------------------------------------------------ 
    # Create tree view dynamically 
        view_arch = dedent("""<?xml version="1.0"?>
                       <tree>""")
        for field_name in field_names:
           view_arch += dedent("""<field name="%s"/>""".strip() % (field_name.name))
           
        view_arch +=  dedent("""</tree>""")
        
           
        print view_arch,'-----------------view_arch +++++++++++++++++++++++++++++++++='
        #return True
        view_id = self.pool.get('ir.ui.view').create(cr, uid, {
                   'name': model_name,
                   'model': model_name,
                   'priority': 16,
                   'type': 'form',
                   'arch': view_arch,
                   'xml_id':"test_emp",
               }, context=context)
       
        print view_id,'---------------view_id'
        action_id = self.pool.get('ir.actions.act_window').create(cr, uid, {
           'name': model_name,
           'view_type': 'tree',
           'view_mode': 'tree',
           'res_model': model_name,
           'usage': 'menu',
           'view_id': view_id,
           }, context=context)
        
        print action_id,'---------------action_id'
        menu_id = self.pool.get('ir.ui.menu').create(cr, uid, {
                   'name': menu_name,
                   'parent_id': parent_menu_id.id,
                   'action': 'ir.actions.act_window,%s' % (action_id)
                   }, context=context)
        print menu_id,'-------------------------menu_id '
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        print '-------------call write method----------- '
        print cr, uid, ids, vals, context,'---------------cr, uid, ids, vals, context'
        res = super(dynamic_xls_report, self).write(cr, uid, ids, vals, context)
        return res
    
    
    def download_report(self, cr, uid, ids, context):
        print '---------------------CALLING MY FINFTION --------------'
        print cr, uid, ids, context,'------------------cr, uid, ids, context--------------'
        report_obj = self.browse(cr, uid,ids[0])
        model_name = report_obj.model_name.model
        field_name = report_obj.field_name.name
        print model_name, field_name,'----------------model_name--------field_name'
        #return True
        return self.get_action(cr, uid, ids, 'dynamic_report.report_download_document', context=context)
        
    def get_xls(self, cr, uid, ids, context=None):
        field_model = self.pool.get('ir.model.fields')
        for val in self.browse(cr, uid, ids):
            model = val.model_name.model
            model_obj = self.pool.get(model)
            field_sel = []
            for field_name in val.field_name:
                field_sel.append(field_name.name)
            if not len(field_sel):
                fld = field_model.search(cr, uid, [('model_id','=',val.model_name.id),('ttype','!=','binary')])
                if len(fld):
                    for f in field_model.browse(cr, uid, fld):
                       field_sel.append(f.name)
                else:
                    raise orm.except_orm(_('Error'), _('No column found to Export'))
            domain = []
            for d_line in val.domain_lines:
                temp = ()
                d_val = str(d_line.value) or False
                if d_val in ('false','False'):
                    d_val = False
                if d_val in ('true','True'):
                    d_val  = True
                temp = (str(d_line.field_name.name),str(d_line.operator),d_val)
                domain.append(temp)
            limit = val.limit_rec or None
            order_field = val.order_on_field and val.order_on_field.name or None
#            if order_field and val.order_type:
#                order = order_field +' desc'
#            elif order_field:
#                order = order_field
#            else:
#                order = None
            try:
                #recs = model_obj.search_read(cr, uid, domain, field_sel, offset=val.set_offset, limit = limit, order =  order )
                recs = model_obj.search_read(cr, uid, domain, field_sel, limit = limit)
            except:
                #mod_ids = model_obj.search(cr, uid, domain, offset=val.set_offset, limit = limit, order =  order )
                mod_ids = model_obj.search(cr, uid, domain, limit = limit)
                recs = model_obj.read(cr, uid, mod_ids,field_sel)
            if not field_sel:
                if recs:
                    field_sel = recs[0].keys()
                else:
                    raise orm.except_orm(_('Error'), _('No record found to Export'))
             
            result = []
            result.append(field_sel)
            for rec in recs:
                value = ''
                temp = []
                for key in field_sel:
                    v = rec.get(key)
                    if v:
                        if type(v) == tuple:
                            #if val.m2m_value:
                            value = v[1]
#                            else:
#                                value = v[0]
                        else:
                            value = str(v)
                            print value,'-----------------value'
                    else:
                        value = v
                    temp.append(value)
                result.append(temp)

            fp = StringIO.StringIO()
            writer = csv.writer(fp)
            for data in result:
                row = []
                for d in data:
                    if isinstance(d, basestring):
                        d = d.replace('\n',' ').replace('\t',' ')
                        try:
                            #d = d.encode('utf-8')
                            d = d.encode('utf-8').strip()
                        except:
                            pass
                    if d is False: d = None
                    row.append(d)
                writer.writerow(row)
        fp.seek(0)
        data = fp.read()
        fp.close()
        out=base64.encodestring(data)
        file_name = str(val.model_name.name) + '.xls'
        self.write(cr, uid, ids, {'filedata':out, 'filename':file_name}, context=context)
        return {
                    'name':'Dynamic Report',
                    'res_model':'dynamic.xls.report',
                    'type':'ir.actions.act_window',
                    'view_type':'form',
                    'view_mode':'tree,form',
                    'target':'current',
                    'nodestroy': True,
                    'context': context,
                    'res_id': ids and ids[0],
                    } 
        
dynamic_xls_report()

class dynamic_domain_line(osv.TransientModel):
    _name = 'dynamic.domain.line'
    _columns = {
                'dynamic_rpt_id': fields.many2one('dynamic.xls.report','Relation Field'),
                'field_name' : fields.many2one('ir.model.fields','Field Name',domain="[('model_id','=',parent.model_name)]"),
                'operator': fields.selection([('ilike','Contains'),('=','Equal'),('!=','Not Equal'),('<','Less Than'),('>','Greater Than'),('<=','Less Than Equal To'),('>=','Greater Than Equal To')],'Operator'),
                'value' : fields.char('Value',help='For relation use dot(.) with field name'),
                }