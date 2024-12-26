import hashlib
import datetime

from flask import redirect, flash
from flask_admin import Admin, BaseView, expose
from sqlalchemy import func
from flask_wtf import FlaskForm
from sqlalchemy.dialects.mysql import NVARCHAR
from wtforms import IntegerField, StringField, validators
from wtforms.fields.simple import TextAreaField
from wtforms.widgets.core import TextArea

from app import app, db, dao
from flask_admin.contrib.sqla import ModelView
from app.models import NhanVien, HocSinh, DanhSachLop, GiaoVienDayHoc, MonHoc, GiaoVien, PhongHoc, QuyDinh, HocKy

admin = Admin(app=app, name='Người Quản Trị', template_mode='bootstrap4')

class MonHocForm(FlaskForm):
    tenMonHoc = StringField('Môn')
    soCot15p = IntegerField('Số cột 15p')
    soCot1Tiet = IntegerField('Số cột 1 tiết')
    soCotThi = IntegerField('Số cột thi')

    def __init__(self, *args, **kwargs):
        super(MonHocForm, self).__init__(*args, **kwargs)
        quy_dinh = QuyDinh.query.first()
        if quy_dinh: #Kiểm tra quy định có tồn tại hay không
            self.soCot15p.validators = [validators.NumberRange(min=1, max=quy_dinh.so_cot_15p)]
            self.soCot1Tiet.validators = [validators.NumberRange(min=1, max=quy_dinh.so_cot_1tiet)]
            self.soCotThi.validators = [validators.NumberRange(min=1, max=quy_dinh.so_cot_thi)]

class MonHocView(ModelView):
    column_list = ['tenMonHoc','soCot15p','soCot1Tiet','soCotThi']
    column_labels = {
        'tenMonHoc':'Môn',
        'soCot15p':'Số cột 15p',
        'soCot1Tiet':'Số cột 1 tiết',
        'soCotThi':'Số cột thi'
    }
    form = MonHocForm

class PhongHocForm(FlaskForm):
    tenPhong = IntegerField('Số phòng', validators=[validators.NumberRange(min=1)])

class PhongHocView(ModelView):
    column_list = ['tenPhong']
    column_labels = {'tenPhong':'Số phòng'}
    form = PhongHocForm

class DanhSachLopView(ModelView):
    form_columns = ['tenLop', 'hocKy', 'giaoVienChuNhiem', 'phongHoc', 'siSo', 'active']
    column_list = ['tenLop', 'hocKy.namHoc', 'giaoVienChuNhiem', 'phongHoc', 'siSoHienTai', 'siSo', 'active']
    column_labels = {
        'tenLop':'Lớp',
        'hocKy.namHoc': 'Năm học',
        'giaoVienChuNhiem':'Giáo viên chủ nhiệm',
        'phongHoc':'Phòng',
        'siSoHienTai':"Sĩ số lớp",
        'siSo':'Sĩ số tối đa',
        'active':'Trạng thái'
    }
    can_create = False

    def can_edit(self, obj):
        # Kiểm tra nếu active là False thì không cho sửa
        return obj.active


    def edit_form(self, obj=None):
        form = super(DanhSachLopView, self).edit_form(obj)
        current_year = datetime.datetime.now().year
        # Lọc các học kỳ của năm hiện tại
        form.hocKy.query_factory = lambda: HocKy.query.filter(
            func.substr(HocKy.namHoc, 1, 4) == str(current_year)
        ).all()
        return form

    def get_query(self):
        return self.session.query(self.model).order_by(self.model.active.desc(), self.model.tenLop)

class GiaoVienView(ModelView):
    column_list = ['hoTen', 'gioiTinh', 'ngaySinh', 'diaChi', 'SDT', 'eMail', 'monHoc', 'taiKhoan', 'matKhau']
    form_columns = ['hoTen', 'gioiTinh', 'ngaySinh', 'diaChi', 'SDT', 'eMail', 'taiKhoan', 'matKhau', 'monHoc']
    column_labels = {
        'hoTen': 'Họ tên',
        'gioiTinh': 'Giới tính',
        'ngaySinh': 'Ngày sinh',
        'diaChi': 'Địa chỉ',
        'SDT': 'Số điện thoại',
        'eMail': 'Email',
        'monHoc': 'Môn học',
        'taiKhoan': 'Tài khoản ',
        'matKhau': 'Mật khẩu'
    }

    def on_model_change(self, form, model, is_created):
        if form.matKhau.data:
            model.matKhau = hashlib.md5(form.matKhau.data.encode('utf-8')).hexdigest()

        super(GiaoVienView, self).on_model_change(form, model, is_created)

class NhanVienView(ModelView):
    #form_columns = ['hoTen', 'gioiTinh', 'ngaySinh', 'diaChi', 'SDT', 'eMail', 'taiKhoan', 'matKhau', 'vaiTro']

    column_labels = {
        'hoTen': 'Họ tên',
        'gioiTinh': 'Giới tính',
        'ngaySinh': 'Ngày sinh',
        'diaChi': 'Địa chỉ',
        'SDT': 'Số điện thoại',
        'eMail': 'Email',
        'taiKhoan': 'Tài khoản',
        'matKhau': 'Mật khẩu',
        'vaiTro': 'Vai trò'
    }

    def on_model_change(self, form, model, is_created):
        if form.matKhau.data:
            model.matKhau = hashlib.md5(form.matKhau.data.encode('utf-8')).hexdigest()

        super(NhanVienView, self).on_model_change(form, model, is_created)

class GiaoVienDayHocView(ModelView):
    column_list = ['hoc_ky.namHoc', 'giaoVien', 'giaoVien.monHoc', 'lopDay']
    column_labels = {
        'hoc_ky.namHoc': 'Năm học',
        'giaoVien': 'Giáo Viên',
        'lopDay': 'Lớp',
        'giaoVien.monHoc': 'Môn Học'
    }

    can_create = False
    can_edit = False

    def get_query(self):
        # Thực hiện sắp xếp năm học giảm dần
        return (
            self.session.query(self.model)
            .join(HocKy, HocKy.idHocKy == self.model.idHocKy)  # JOIN với bảng HocKy
            .order_by(HocKy.namHoc.desc())  # Sắp xếp theo năm học giảm dần
        )


class HocSinhView(ModelView):
    form_columns = ['hocSinhLop', 'hoTen', 'gioiTinh','ngaySinh', 'khoi','diaChi','SDT','eMail']
    column_list = ['hoTen', 'gioiTinh', 'ngaySinh', 'khoi','diaChi','SDT','eMail','hocSinhLop']
    column_labels = {
        'hoTen': 'Họ tên',
        'gioiTinh': 'Giới tính',
        'ngaySinh': 'Ngày sinh',
        'khoi':'Khối',
        'diaChi':'Địa chỉ',
        'SDT':'Số điện thoại',
        'hocSinhLop':'Học lớp'
    }
    can_create = False  # Không cho phép thêm

    def get_query(self):
        # Sắp xếp active = True trước, sau đó theo tên lớp
        return self.session.query(self.model).order_by(self.model.khoi.desc())

class QuiDinhForm(FlaskForm):
    min_age = IntegerField('Tuổi thấp nhất', validators=[validators.NumberRange(min=1)])
    max_age = IntegerField('Tuổi cao nhất', validators=[validators.NumberRange(min=1)])
    si_so = IntegerField('Sĩ số', validators=[validators.NumberRange(min=1)])
    so_cot_15p = IntegerField('Số cột 15p', validators=[validators.NumberRange(min=1)])
    so_cot_1tiet = IntegerField('Số cột 1 tiết', validators=[validators.NumberRange(min=1)])
    so_cot_thi = IntegerField('Số cột thi', validators=[validators.NumberRange(min=1)])

class QuiDinhView(ModelView):
    column_labels = {
        'min_age': 'Tuổi thấp nhất',
        'max_age': 'Tuổi cao nhất',
        'si_so': 'Sĩ số',
        'so_cot_15p': 'Số cột 15p',
        'so_cot_1tiet': 'Số cột 1 tiết',
        'so_cot_thi': 'Số cột thi'
    }
    can_create = False
    can_delete = False

    form=QuiDinhForm

    form_columns = ['min_age', 'max_age', 'si_so', 'so_cot_15p', 'so_cot_1tiet','so_cot_thi']
    column_list = ['min_age', 'max_age', 'si_so', 'so_cot_15p', 'so_cot_1tiet','so_cot_thi']

admin.add_view(QuiDinhView(QuyDinh, db.session))
admin.add_view(MonHocView(MonHoc, db.session))
admin.add_view(PhongHocView(PhongHoc, db.session))
admin.add_view(NhanVienView(NhanVien, db.session))
admin.add_view(GiaoVienView(GiaoVien, db.session))
admin.add_view(GiaoVienDayHocView(GiaoVienDayHoc, db.session))
admin.add_view(HocSinhView(HocSinh, db.session))
admin.add_view(DanhSachLopView(DanhSachLop, db.session))

