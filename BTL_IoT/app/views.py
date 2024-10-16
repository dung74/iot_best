from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse 
from .models import *
import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate,login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Monitor
from paho.mqtt.client import Client  # Thư viện MQTT
from .models import DeviceState, History  # Model lưu trạng thái thiết bị
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import time
import pandas as pd
import plotly.express as px
from django.db.models import Q

def profile(request):
    context = {}
    return render(request, 'app/html/profile.html', context)

def home(request):
    device_states  = DeviceState.objects.all()
    
    return render(request, 'app/html/home.html', {'device_states': device_states})

def history(request):
    
    lich_su_list = History.objects.all().order_by('-timestamp')

    time_query = request.GET.get('time_query', '')
    
         # Lấy page_size từ request, nếu không có thì mặc định là 10
    page_size = request.GET.get('page_size', request.session.get('page_size', 10))
    if time_query:
        try:
            # Chuyển đổi chuỗi 'dd/mm/yyyy' hoặc 'dd/mm/yyyy HH:MM:SS' sang datetime
            if len(time_query) == 10:  # Nếu chỉ nhập ngày 'dd/mm/yyyy'
                date_query = datetime.strptime(time_query, "%d/%m/%Y")
                lich_su_list = lich_su_list.filter(
                    timestamp__year=date_query.year,
                    timestamp__month=date_query.month,
                    timestamp__day=date_query.day
                )
            else:  # N
                # Chuyển đổi định dạng từ "dd/mm/yyyy HH:MM:SS" sang datetime
                time_query = datetime.strptime(time_query, '%d/%m/%Y %H:%M:%S')
                lich_su_list = lich_su_list.filter(timestamp__icontains=time_query)
        except ValueError:
            # Xử lý nếu không thể chuyển đổi
            pass

        if time_query:
            lich_su_list = lich_su_list.filter(timestamp__icontains=time_query)

    # Lưu page_size vào session
    request.session['page_size'] = page_size

    try:
        page_size = int(page_size)
        if page_size<=0:
            page_size = 10
    except ValueError:
        page_size = 10



    paginator = Paginator(lich_su_list, page_size) 
    page_number = request.GET.get('page',1)
    page_obj = paginator.get_page(page_number)

    for item in page_obj:
        item.timestamp = item.timestamp.strftime('%d/%m/%Y %H:%M:%S')  # Định dạng ngày/tháng/năm giờ:phút:giây

    context = {
        'page_obj': page_obj,
        'page_size': page_size,
        
        'time_query': time_query,

    }

    return render(request,'app/html/history.html', context)



def monitor(request):
    monitor_list = Monitor.objects.all().order_by('-timestamp')

    # Lấy giá trị tìm kiếm từ các input trong form
    temperature_query = request.GET.get('temperature_query', '')
    humidity_query = request.GET.get('humidity_query', '')
    light_intensity_query = request.GET.get('light_intensity_query', '')
    time_query = request.GET.get('time_query', '')

    if time_query:
        try:
            # Chuyển đổi chuỗi 'dd/mm/yyyy' hoặc 'dd/mm/yyyy HH:MM:SS' sang datetime
            if len(time_query) == 10:  # Nếu chỉ nhập ngày 'dd/mm/yyyy'
                date_query = datetime.strptime(time_query, "%d/%m/%Y")
                monitor_list = monitor_list.filter(
                    timestamp__year=date_query.year,
                    timestamp__month=date_query.month,
                    timestamp__day=date_query.day
                )
            else:  # N
                # Chuyển đổi định dạng từ "dd/mm/yyyy HH:MM:SS" sang datetime
                time_query = datetime.strptime(time_query, '%d/%m/%Y %H:%M:%S')
                monitor_list = monitor_list.filter(timestamp__icontains=time_query)
        except ValueError:
            # Xử lý nếu không thể chuyển đổi
            pass
    # Thực hiện tìm kiếm riêng lẻ cho từng trường
    if temperature_query:
        monitor_list = monitor_list.filter(temperature__icontains=temperature_query)
    
    if humidity_query:
        monitor_list = monitor_list.filter(humidity__icontains=humidity_query)

    if light_intensity_query:
        monitor_list = monitor_list.filter(light_intensity__icontains=light_intensity_query)
    
    if time_query:
        monitor_list = monitor_list.filter(timestamp__icontains=time_query)




    # Pagination
    page_size = request.GET.get('page_size', request.session.get('page_size', 10))
    request.session['page_size'] = page_size
    try:
        page_size = int(page_size)
        if page_size <= 0:
            page_size = 10
    except ValueError:
        page_size = 10

    
    paginator = Paginator(monitor_list, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
   
    for item in page_obj:
        item.timestamp = item.timestamp.strftime('%d/%m/%Y %H:%M:%S')  # Định dạng ngày/tháng/năm giờ:phút:giây

    context = {
        'page_obj': page_obj,
        'page_size': page_size,
        'temperature_query': temperature_query,
        'humidity_query': humidity_query,
        'light_intensity_query': light_intensity_query,
        'time_query': time_query,

    }

    return render(request, 'app/html/monitor.html', context)



def publish_mqtt_command(device_name, state):
    client = Client()
    client.username_pw_set(username="dungx", password="1234567")
    client.connect("localhost", 1884, 60)
    
    # Publish lệnh MQTT
    message = f"{device_name} {'ON' if state else 'OFF'}"
    client.publish("ledControll", message)
    client.loop_start()     

@csrf_exempt
def toggle_device(request):
    if request.method =='POST':
        device_name = request.POST.get('device_name')
        state = request.POST.get('state') == 'true'
        if device_name == None:
            data = json.loads(request.body)  
            device_name = data.get('device_name')  
            state = data.get('state') == 'true'  
        if device_name =="Bóng Đèn":
            device = 'LED1'
        elif device_name =="Quạt":
            device = 'LED2'
        elif device_name =="Điều Hòa":
            device = 'LED3'
        # chuaxong

        
        # try:
        #     device_state = DeviceState.objects.get(device_name=device_name)
        #     device_state.state = state
        #     device_state.save()
        # except DeviceState.DoesNotExist:
        #     DeviceState.objects.create(device_name=device_name, state=state)

        History.objects.create(
            device = device_name,
            state = 'Bật' if state else 'Tắt',
            timestamp = timezone.now()

        )
        # Publish lệnh MQTT để điều khiển thiết bị
        publish_mqtt_command(device, state)
        time.sleep(0.5)
        return JsonResponse({'status': 'success'})

    # Trả về phản hồi lỗi nếu không phải phương thức POST
    return JsonResponse({'status': 'failed'}, status=400)

def get_device_state(request):
    if request.method == 'GET':
        device_name = request.GET.get('device_name')

        if not device_name:
            return JsonResponse({'error': 'Device name is required'}, status=400)

        # Tìm kiếm thiết bị trong cơ sở dữ liệu
        device = DeviceState.objects.filter(device_name=device_name).first()

        if device:
            # Trả về trạng thái thiết bị: 'on' nếu state = 1, 'off' nếu state = 0
            return JsonResponse({'state': 'on' if device.state == 1 else 'off'})
        else:
            return JsonResponse({'error': 'Device not found'}, status=404)
# lay data cho bieu do
def get_sensor_data(request):
    data = list(Monitor.objects.values('timestamp', 'temperature', 'humidity', 'light_intensity'))
    return JsonResponse(data, safe=False)


