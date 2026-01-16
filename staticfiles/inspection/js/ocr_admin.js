(function() {
    'use strict';
    
    document.addEventListener('DOMContentLoaded', function() {
        // 检查是否在检验记录的添加/编辑页面
        if (!document.querySelector('.model-inspectionrecord')) return;
        
        // 创建OCR识别按钮
        const ocrButton = document.createElement('button');
        ocrButton.type = 'button';
        ocrButton.className = 'el-button el-button--primary';
        ocrButton.innerHTML = '<i class="el-icon-camera"></i> OCR识别';
        ocrButton.style.cssText = 'margin: 10px 0; padding: 10px 20px; background: #409EFF; color: white; border: none; border-radius: 4px; cursor: pointer;';
        
        // 找到OCR识别区域并插入按钮
        const fieldsets = document.querySelectorAll('fieldset');
        fieldsets.forEach(function(fieldset) {
            const legend = fieldset.querySelector('legend, h2');
            if (legend && legend.textContent.includes('OCR识别')) {
                fieldset.appendChild(ocrButton);
            }
        });
        
        // 如果没找到fieldset，尝试找SimpleUI的结构
        if (!ocrButton.parentElement) {
            const formRows = document.querySelectorAll('.form-row, .el-form-item');
            const plateImageRow = Array.from(formRows).find(row => 
                row.innerHTML.includes('plate_image') || row.innerHTML.includes('车牌号图片')
            );
            if (plateImageRow) {
                plateImageRow.parentElement.insertBefore(ocrButton, plateImageRow.nextSibling);
            }
        }
        
        // OCR识别按钮点击事件
        ocrButton.addEventListener('click', function() {
            const formData = new FormData();
            
            // 获取上传的图片
            const frontInput = document.querySelector('input[name="license_front_image"]');
            const backInput = document.querySelector('input[name="license_back_image"]');
            const plateInput = document.querySelector('input[name="plate_image"]');
            
            if (frontInput && frontInput.files[0]) {
                formData.append('license_front_image', frontInput.files[0]);
            }
            if (backInput && backInput.files[0]) {
                formData.append('license_back_image', backInput.files[0]);
            }
            if (plateInput && plateInput.files[0]) {
                formData.append('plate_image', plateInput.files[0]);
            }
            
            if (!formData.has('license_front_image') && !formData.has('license_back_image') && !formData.has('plate_image')) {
                alert('请先上传至少一张图片');
                return;
            }
            
            ocrButton.disabled = true;
            ocrButton.innerHTML = '<i class="el-icon-loading"></i> 识别中...';
            
            // 获取CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch('/admin/inspection/inspectionrecord/ocr-recognize/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fillFormWithOCRData(data.data);
                    alert('识别成功！请检查并确认表单内容');
                } else {
                    alert('识别失败: ' + data.message);
                }
            })
            .catch(error => {
                alert('请求失败: ' + error.message);
            })
            .finally(() => {
                ocrButton.disabled = false;
                ocrButton.innerHTML = '<i class="el-icon-camera"></i> OCR识别';
            });
        });
        
        // 填充表单数据
        function fillFormWithOCRData(data) {
            const fieldMapping = {
                'license_plate_number': 'license_plate_number',
                'vehicle_type': 'vehicle_type',
                'owner': 'owner',
                'address': 'address',
                'chassis_number': 'chassis_number',
                'engine_number': 'engine_number',
                'brand': 'brand',
                'model_name': 'model_name',
                'registration_date': 'registration_date',
                'issue_date': 'issue_date',
                'issue_authority': 'issue_authority',
                'tractor_min_weight': 'tractor_min_weight',
                'tractor_max_load': 'tractor_max_load',
                'passenger_capacity': 'passenger_capacity',
                'overall_dimension': 'overall_dimension',
                'inspection_record': 'inspection_record'
            };
            
            for (const [dataKey, fieldName] of Object.entries(fieldMapping)) {
                if (data[dataKey]) {
                    const input = document.querySelector(`[name="${fieldName}"]`);
                    if (input) {
                        input.value = data[dataKey];
                        // 触发change事件
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            }
            
            // 存储OCR原始数据
            if (data.ocr_raw_data) {
                const rawDataInput = document.querySelector('[name="ocr_raw_data"]');
                if (rawDataInput) {
                    rawDataInput.value = JSON.stringify(data.ocr_raw_data);
                }
            }
        }
    });
})();
