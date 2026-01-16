function doOCR() {
    var btn = document.getElementById('ocr-btn');
    var formData = new FormData();
    
    // 获取文件输入
    var licenseFont = document.getElementById('id_license_front_image');
    var licenseBack = document.getElementById('id_license_back_image');
    var plateImage = document.getElementById('id_plate_image');
    
    if (licenseFont && licenseFont.files[0]) {
        formData.append('license_front_image', licenseFont.files[0]);
    }
    if (licenseBack && licenseBack.files[0]) {
        formData.append('license_back_image', licenseBack.files[0]);
    }
    if (plateImage && plateImage.files[0]) {
        formData.append('plate_image', plateImage.files[0]);
    }
    
    // 检查是否有文件
    var hasFile = false;
    for (var pair of formData.entries()) {
        hasFile = true;
        break;
    }
    
    if (!hasFile) {
        alert('请先上传图片（行驶证正面、副页或车牌）');
        return;
    }
    
    btn.disabled = true;
    btn.textContent = '识别中...';
    
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch('/admin/inspection/inspectionrecord/ocr-recognize/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            fillForm(data.data);
            alert('识别成功！请检查表单内容');
        } else {
            alert('识别失败: ' + data.message);
        }
    })
    .catch(function(error) {
        alert('请求失败: ' + error.message);
    })
    .finally(function() {
        btn.disabled = false;
        btn.textContent = '🔍 OCR识别';
    });
}

function fillForm(data) {
    var fields = [
        'license_plate_number', 'vehicle_type', 'owner', 'address',
        'chassis_number', 'trailer_frame_number', 'engine_number', 
        'brand', 'model_name', 'registration_date', 'issue_date', 'issue_authority',
        'tractor_min_weight', 'harvester_weight', 'tractor_max_load',
        'passenger_capacity', 'overall_dimension', 'inspection_record',
        'plate_ocr_result'
    ];
    
    fields.forEach(function(field) {
        if (data[field]) {
            var el = document.getElementById('id_' + field);
            if (el) {
                el.value = data[field];
            }
        }
    });
}
