from odoo import api, fields, models, _
import sys
import traceback
from datetime import datetime, timedelta
import pytz
from odoo.exceptions import UserError, ValidationError
from ..zk import ZK, const
from ..zk.user import User
from ..zk.finger import Finger
from ..zk.attendance import Attendance
from ..zk.exception import ZKErrorResponse, ZKNetworkError

sys.path.append("zk")


class BasicException(Exception):
    pass


class BiometricDeviceConfig(models.Model):
    _name = 'biometric.config'

    name = fields.Char(string='Name', required=True)
    device_ip = fields.Char(string='Device IP', required=True)
    port = fields.Integer(string='Port', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def test_device_connection(self):
        """test connection with device"""
        conn = None
        zk = ZK(self.device_ip, port=self.port, timeout=1000, password=0, force_udp=False, verbose=False)

        try:
            print('Connecting to device ...')
            conn = zk.connect()
            print('SDK build=1      : %s' % conn.set_sdk_build_1())  # why?
            print('Disabling device ...')
            conn.disable_device()
            fmt = conn.get_extend_fmt()
            print('ExtendFmt        : {}'.format(fmt))
            fmt = conn.get_user_extend_fmt()
            print('UsrExtFmt        : {}'.format(fmt))
            print('Face FunOn       : {}'.format(conn.get_face_fun_on()))
            print('Face Version     : {}'.format(conn.get_face_version()))
            print('Finger Version   : {}'.format(conn.get_fp_version()))
            print('Old Firm compat  : {}'.format(conn.get_compat_old_firmware()))
            net = conn.get_network_params()
            print('IP:{} mask:{} gateway:{}'.format(net['ip'], net['mask'], net['gateway']))
            now = datetime.today().replace(microsecond=0)
            conn.set_time(datetime.now() + timedelta(hours=5, minutes=30))
            zk_time = conn.get_time()
            dif = abs(zk_time - datetime.now()+ timedelta(hours=5, minutes=30)).total_seconds()
            print('Time             : {}'.format(zk_time))
            if dif > 120:
                print("WRN: TIME IS NOT SYNC!!!!!! (local: %s) use command -u to update" % now)
            print('Firmware Version : {}'.format(conn.get_firmware_version()))
            print('Platform         : %s' % conn.get_platform())
            print('DeviceName       : %s' % conn.get_device_name())
            print('Pin Width        : %i' % conn.get_pin_width())
            print('Serial Number    : %s' % conn.get_serialnumber())
            print('MAC: %s' % conn.get_mac())
            print('')
            print('--- sizes & capacity ---')
            conn.read_sizes()
            print(conn)
            print('')

            print ("Voice Test ...")
            conn.test_voice(0)
            print ('Enabling device ...')
            conn.enable_device()
            raise UserError(_("Connection Success"))
        except BasicException as e:
            print (e)
            print ('')
            raise UserError(_(e))
        except Exception as e:
            print("Process terminate : {}".format(e))
            print("Error: %s" % sys.exc_info()[0])
            print('-' * 60)
            traceback.print_exc(file=sys.stdout)
            print('-' * 60)
            raise UserError(_(e))
        finally:
            if conn:
                print('Enabling device ...')
                conn.enable_device()
                conn.disconnect()
                print('ok bye!')
                print('')

    def sync_employees(self):
        """syncing employees with device"""
        conn = None
        zk = ZK(self.device_ip, port=self.port, timeout=1000, force_udp=False, verbose=False)

        try:
            employees = self.env['hr.employee'].search([])
            for employee in employees:
                conn = zk.connect()
                conn.disable_device()
                conn.set_user(uid=employee.id, name=str(employee.name), privilege=0, password='',
                              user_id=str(employee.id))
                print('User Added')
            conn.enable_device()
            raise UserError(_("Sync Employee Success"))
        except Exception as e:
            print("Process terminate : {}".format(e))
            conn.enable_device()

    def delete_users(self):
        """delete users from the device"""
        conn = None
        zk = ZK(self.device_ip, port=self.port, timeout=1000, password=0, force_udp=False, verbose=False)

        try:
            employees = self.env['hr.employee'].search([])
            for employee in employees:
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

    def sync_time(self):
        """sync time of device with server time"""
        conn = None
        zk = ZK(self.device_ip, port=self.port)
        try:
            conn = zk.connect()
            print("Syncing time...")
            conn.set_time(datetime.now()+ timedelta(hours=5, minutes=30))
        except Exception as e:
            print("Process terminate : {}".format(e))
        finally:
            if conn:
                conn.disconnect()

    def download_attendance_log(self):
        """downloading attendance log to the database from device"""
        attend_obj = self.env['attendance.log']
        ip = self.device_ip
        port = self.port
        conn = None
        zk = ZK(ip, port, timeout=1000, password=0, force_udp=False, verbose=False)
        try:
            conn = zk.connect()
            conn.disable_device()
            attendances = conn.get_attendance()
            conn.enable_device()
            count = 0
            if attendances:
                for attendance in attendances:
                    employee_id = int(str(attendance).split(':')[1].strip())
                    punching_date = str(attendance).split(':')[2].split(' ')[1]
                    punching_time = str(attendance).split(':')[2].split(' ')[2] + ':' + str(attendance).split(':')[3] +':'+ str(attendance).split(':')[4].split('(')[0].split(' ')[0]
                    punching_datetime = datetime.strptime(punching_date + ' ' + punching_time, '%Y-%m-%d %H:%M:%S') - timedelta(hours=5, minutes=30)
                    existing_record = attend_obj.search([('employee_id', '=', employee_id), ('punching_time', '=', str(punching_datetime))])
                    if existing_record:
                        pass
                    else:
                        employee = self.env['hr.employee'].sudo().search([('id', '=', employee_id)])
                        if employee and employee_id:
                            count += 1
                            print(count)
                            vals = {
                                'employee_id': employee_id,
                                'punching_time': punching_datetime,
                                'date': datetime.strptime(punching_date + ' ' + punching_time, '%Y-%m-%d %H:%M:%S').date(),
                                'status': str(attendance).split(' ')[6].split(')')[0] if
                                str(attendance).split(' ')[6].split(')')[0] in ['0', '1'] else '255',
                                'device': self.id,
                                'is_calculated': False
                            }
                            attend_obj.create(vals)
                return{'name': 'Success Message',
                       'type': 'ir.actions.act_window',
                       'res_model': 'success.wizard',
                       'view_mode': 'form',
                       'target': 'new'}
            else:
                print('No attendance data')
                raise UserError(_("No attendance data to download"))
        except Exception as e:
            print("Process terminate : {}".format(e))
            raise UserError(_(e))
        finally:
            if conn:
                conn.disconnect()
        return True
