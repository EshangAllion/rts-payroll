from odoo import api, fields, models, _
import sys
import traceback
import datetime
import pytz
from odoo.exceptions import UserError, ValidationError
from ..zk import ZK, const
from ..zk.user import User
from ..zk.finger import Finger
from ..zk.attendance import Attendance
from ..zk.exception import ZKErrorResponse, ZKNetworkError

sys.path.append("zk")


class BiometricDeviceWizard(models.TransientModel):
    _name = 'biometric.device.wizard'
    
    biometric_id = fields.Many2one('biometric.config', string='Biometric Device', required=True)
    opertaion_type = fields.Selection([('update', 'Update'),
                                       ('delete', 'Delete')], string="Type")

    def confirm_update_with_biometric(self):
        employee_id = self._context.get('active_id')
        employee_obj = self.env['hr.employee'].browse(employee_id)
        ip = self.biometric_id.device_ip
        port = self.biometric_id.port
        conn = None
        zk = ZK(ip, port=port, timeout=1000, force_udp=False, verbose=False)
        try:
            conn = zk.connect()
            conn.disable_device()
            conn.set_user(uid=employee_obj.id, name=str(employee_obj.name), privilege=0, password='',
                          user_id=str(employee_obj.id))
            print('User Added')
            conn.enable_device()
            raise UserError(_("Sync Employee Success"))
        except Exception as e:
            print("Process terminate : {}".format(e))
            conn.enable_device()
            # raise UserError(_(e))

    def confirm_scan_with_biometric(self):
        employee_id = self._context.get('active_id')
        ip = self.biometric_id.device_ip
        port = self.biometric_id.port
        conn = None
        zk = ZK(ip, port=port, timeout=1000, force_udp=False, verbose=False)

        try:
            employee_id_list = []
            conn = zk.connect()
            # conn.disable_device()
            users = conn.get_users()
            for user in users:
                device_user_id = int(format(user.uid))
                employee_id_list.append(device_user_id)
            in_the_list = employee_id in employee_id_list
            if in_the_list == True:
                print('Place your finger')
                zk.enroll_user(employee_id)
            else:
                raise UserError(_("Please sync the employee and try again later"))
        except Exception as e:
            print("Process terminate : {}".format(e))
            raise UserError(_(e))


    def confirm_delete_with_biometric(self):
        employee_id = self._context.get('active_id')
        employee_obj = self.env['hr.employee'].browse(employee_id)
        ip = self.biometric_id.device_ip
        port = self.biometric_id.port
        conn = None
        zk = ZK(ip, port=port, timeout=1000, password=0, force_udp=False, verbose=False)

        try:
            for employee in employee_obj:
                conn = zk.connect()
                conn.disable_device()
                conn.delete_user(uid=employee.id)
                conn.enable_device()
                print('User Deleted')
            raise UserError(_("Device User Deletion Successful"))
        except Exception as e:
            print("Process terminate : {}".format(e))
            raise UserError(_(e))
        finally:
            if conn:
                conn.disconnect()
    

class SuccessWizard(models.TransientModel):
    _name = 'success.wizard'