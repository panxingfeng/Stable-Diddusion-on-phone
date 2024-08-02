import base64
import io
import logging
import os
import random
import re
import string
import time
from asyncio import Queue

import requests
from PIL import Image

import webuiapi

api = webuiapi.WebUIApi(host='127.0.0.1', port=7860)
api.set_auth('panllq', 'Pan.960327')

API_URL = 'http://127.0.0.1:7860'
HEADERS = {
    "Authorization": "Basic cGFubGxxOlBhbi45NjAzMjc="
}

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)

# 任务ID列表
task_id_list = []
task_queue = Queue()
tasks_in_progress = {}
current_task_id = None

tasks = {}
#图像反推的方法体
def set_chrome_window_position():
    import pygetwindow as gw
    import pyautogui

    # 获取所有标题中包含“Chrome”的窗口
    windows = gw.getWindowsWithTitle('Chrome')
    if windows:
        chrome_window = windows[0]
        # 获取屏幕宽高
        screen_width, screen_height = pyautogui.size()
        # 设置Chrome窗口的宽高
        chrome_width, chrome_height = 800, 1200
        chrome_window.resizeTo(chrome_width, chrome_height)
        # 将Chrome窗口移动到屏幕的右下角
        chrome_window.moveTo(screen_width - chrome_width, screen_height - chrome_height)


def click_button(driver, ID):
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    wait = WebDriverWait(driver, 60)
    try:
        # 等待按钮出现并点击
        generate_button = wait.until(
            EC.presence_of_element_located((By.ID, ID))
        )
        generate_button.click()
    except Exception as e:
        print(f"点击生成按钮时遇到异常: {e}")


def input_image(driver, upload_div, filepath):
    from selenium.webdriver.common.by import By

    try:
        # 查找文件输入框并上传文件
        file_input = upload_div.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(filepath)
    except Exception as e:
        print(f"使用CSS Selector定位文件输入框失败: {e}")
        raise e


def get_top_30_texts_with_confidence_above_threshold(driver, threshold=0.1, max_scan_time=2):
    from selenium.webdriver.common.by import By
    import time

    try:
        start_time = time.time()
        # 获取所有包含置信度的元素集
        confidence_sets = driver.find_elements(By.CSS_SELECTOR, ".confidence-set.group.svelte-75gm11")
        result_texts = []
        processed_count = 0
        start_index = 2  # 跳过前两个元素

        # 遍历所有置信度元素集
        for set_index, set in enumerate(confidence_sets):
            if processed_count >= 30:
                break
            if time.time() - start_time > max_scan_time:
                break
            # 获取文本和置信度元素
            texts = set.find_elements(By.CSS_SELECTOR, ".text.svelte-75gm11")
            confidences = set.find_elements(By.CSS_SELECTOR, ".confidence.svelte-75gm11")

            # 遍历文本和置信度，筛选置信度高于阈值的文本
            for text, confidence in zip(texts[start_index:], confidences[start_index:]):
                confidence_value = confidence.text.strip('%')
                if confidence_value:
                    confidence_value = float(confidence_value)
                    if confidence_value > (threshold * 100):
                        result_texts.append(text.text)
                        processed_count += 1
                        if processed_count >= 30:
                            break

            start_index = max(0, start_index - len(texts))

        return result_texts
    except Exception as e:
        print("获取值时遇到异常:", e)
    return []


def generate_image_from_image(filepath):
    global driver, texts_above_threshold
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    try:
        options = Options()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        driver = webdriver.Chrome(options=options)
        set_chrome_window_position()
        driver.get('http://127.0.0.1:7860')

        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'WD 1.4 标签器')]"))
        ).click()

        upload_div = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "tab_tagger"))
        )

        input_image(driver, upload_div, filepath)
        while True:
            texts_above_threshold = get_top_30_texts_with_confidence_above_threshold(driver)
            if texts_above_threshold:
                logging.debug(f"Texts above threshold: {texts_above_threshold}")
                return texts_above_threshold

    except Exception as e:
        logging.error(f"Error generating image: {e}")
    finally:
        driver.quit()


#图像反推
#########################################################################################


def check_progress():
    global current_task_id
    while True:
        if current_task_id is not None:
            try:
                progress_response = requests.get(f'{API_URL}/sdapi/v1/progress', headers=HEADERS, timeout=180)
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    eta_relative = progress_data.get('eta_relative', None)
                    progress = progress_data.get('progress', 0.0)
                    # 更新任务进度
                    tasks_in_progress[current_task_id]['progress'] = progress
                    # 检查机器是否空闲
                    if eta_relative == 0.0 and progress == 0.0:
                        print("Machine is idle, checking for next task.")
                        tasks_in_progress[current_task_id]['status'] = 'completed'
                        task_id_list.remove(current_task_id)  # 从任务ID列表中删除已完成的任务
                        current_task_id = None  # 当前任务完成，设置为 None 以开始下一个任务
                else:
                    tasks_in_progress[current_task_id]['status'] = 'failed'
            except Exception as e:
                tasks_in_progress[current_task_id]['status'] = f'failed: {str(e)}'
                print(f"Exception in task {current_task_id}: {e}")

        if current_task_id is None and not task_queue.empty():
            # 当前没有任务，且队列不为空，启动下一个任务
            current_task_id, task_data = task_queue.get()
            tasks_in_progress[current_task_id] = {'status': 'in progress', 'progress': 0.0}
            print(f"Started processing task {current_task_id}")

            try:
                # 调用 /generate_images 端点生成图像
                generate_response = requests.post('https://panllq.cpolar.top/generate_images', json=task_data,
                                                  headers=HEADERS, timeout=180)
                print("generate_response:", generate_response)
                if generate_response.status_code == 200:
                    result = generate_response.json()
                    tasks_in_progress[current_task_id]['images'] = result.get('images', [])
                    tasks_in_progress[current_task_id]['info_texts'] = result.get('info_texts', [])
                    tasks_in_progress[current_task_id]['seed'] = [extract_seed(info_text) for info_text in
                                                                  result.get('info_texts', [])]
                    tasks_in_progress[current_task_id]['status'] = 'completed'
                    print(f"Generated images for task {current_task_id}")
                else:
                    tasks_in_progress[current_task_id]['status'] = 'failed'
                    print(f"Failed to generate images for task {current_task_id}")

                task_id_list.remove(current_task_id)  # 从任务ID列表中删除已完成的任务
                current_task_id = None  # 任务完成，设置为 None 以开始下一个任务
                task_queue.task_done()
                continue  # 继续处理队列中的下一个任务
            except Exception as e:
                tasks_in_progress[current_task_id]['status'] = f'failed: {str(e)}'
                print(f"Exception in task {current_task_id}: {e}")
                current_task_id = None
                task_queue.task_done()
                continue

        time.sleep(5)  # 每5秒检查一次任务进度



def generate_random_filename(extension=".png"):
    """生成一个随机文件名"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16)) + extension

# 将 base64 字符串转换为 PIL 图像对象
def base64_to_image(base64_str, output_dir):
    # 去掉 base64 前缀
    if base64_str.startswith('data:image'):
        base64_str = base64_str.split(',')[1]

    try:
        # 解码 base64 字符串为字节数据
        image_data = base64.b64decode(base64_str)
        # 将字节数据加载为 PIL 图像对象
        image = Image.open(io.BytesIO(image_data))

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        # 生成随机文件名
        filename = generate_random_filename() + '.png'
        file_path = os.path.join(output_dir, filename)

        # 保存图像到本地
        image.save(file_path)

        return image
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def extract_seed(info_text):
    seed_regex = r"Seed:\s*(\d+)"
    match = re.search(seed_regex, info_text)
    if match:
        return match.group(1)
    return None


def moRen(translated_prompt, translated_negativePrompt, seed, style, cfg_scale, sample, steps, width, height,
          image_count, sd_model_checkpoint, vae, skip_layers):
    result = api.txt2img(
        prompt=translated_prompt,
        negative_prompt=translated_negativePrompt,
        seed=int(seed),
        styles=[style],
        cfg_scale=cfg_scale,
        sampler_index=sample,
        sampler_name=sample,
        steps=steps,
        batch_size=image_count,
        width=width,
        height=height,
        override_settings={
            "sd_model_checkpoint": sd_model_checkpoint,
            "sd_vae": vae,
            "CLIP_stop_at_last_layers": int(int(skip_layers))
        },
    )
    response_data = result.json
    return response_data


def aDetailerMethod(aDetailers, translated_prompt, translated_negativePrompt, seed, style, cfg_scale, sample, steps,
                    width,
                    height, image_count, sd_model_checkpoint, vae, skip_layers):
    # 处理adetailer
    adetailer_units = []
    for adetailer in aDetailers:
        model = adetailer.get('model')
        if model != "None":
            ads = webuiapi.ADetailer(ad_model=model)
            adetailer_units.append(ads)
    result = api.txt2img(
        prompt=translated_prompt,
        # model_info[11]:模型推荐正面tag
        negative_prompt=translated_negativePrompt,
        # model_info[12]:模型推荐负面tag,
        seed=int(seed),
        styles=[style],
        cfg_scale=cfg_scale,
        sampler_index=sample,
        sampler_name=sample,
        steps=steps,
        batch_size=image_count,
        width=width,
        height=height,
        override_settings={
            "sd_model_checkpoint": sd_model_checkpoint,
            "sd_vae": vae,
            "CLIP_stop_at_last_layers": int(skip_layers)
        },
        adetailer=adetailer_units
    )
    response_data = result.json
    return response_data


def high_res(high_res_method, translated_prompt, translated_negativePrompt, seed, style, cfg_scale, sample, steps,
             upscale, high_res_steps, width, height, denoise, image_count, sd_model_checkpoint, vae, skip_layers):
    global result
    if high_res_method == "Latent":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.Latent,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    elif high_res_method == "ESRGAN_4x":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.ESRGAN_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    elif high_res_method == "R-ESRGAN 4x+":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.R_ESRGAN,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    elif high_res_method == "R-ESRGAN 4x+ Anime6B":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.ESRGAN_4x_Anime6B,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    elif high_res_method == "SwinIR_4x":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.SwinIR_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    elif high_res_method == "4x-UltraShar":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.UltraShar_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    response_data = result.json
    return response_data


def controlNetMethod(controlNets, translated_prompt, translated_negativePrompt, seed, style, cfg_scale, sample, steps,
                     width, height, image_count, sd_model_checkpoint, vae, skip_layers):
    # 获取并解码 base64 图像
    controlnet_units = []
    unit1 = unit2 = unit3 = None
    if controlNets[0].get('model_value'):
        preprocessor1 = controlNets[0]['preprocessor']
        model_value1 = controlNets[0]['model_value']
        imageData1 = controlNets[0]['image']
        controlWeight1 = controlNets[0]['controlWeight']
        startTime1 = controlNets[0]['startTime']
        endTime1 = controlNets[0]['endTime']
        if imageData1:
            image1 = base64_to_image(imageData1, "E://output//upload")
            unit1 = webuiapi.ControlNetUnit(image=image1, module=preprocessor1, model=model_value1,
                                            weight=float(controlWeight1), guidance_start=startTime1,
                                            guidance_end=endTime1, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit1)

    if controlNets[1].get('model_value'):
        preprocessor2 = controlNets[1]['preprocessor']
        model_value2 = controlNets[1]['model_value']
        imageData2 = controlNets[1]['image']
        controlWeight2 = controlNets[0]['controlWeight']
        startTime2 = controlNets[0]['startTime']
        endTime2 = controlNets[0]['endTime']
        if imageData2:
            image2 = base64_to_image(imageData2, "E://output//upload")
            unit2 = webuiapi.ControlNetUnit(image=image2, module=preprocessor2, model=model_value2,
                                            weight=float(controlWeight2), guidance_start=startTime2,
                                            guidance_end=endTime2, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit2)

    if controlNets[2].get('model_value'):
        preprocessor3 = controlNets[2]['preprocessor']
        model_value3 = controlNets[2]['model_value']
        imageData3 = controlNets[2]['image']
        controlWeight3 = controlNets[0]['controlWeight']
        startTime3 = controlNets[0]['startTime']
        endTime3 = controlNets[0]['endTime']
        if imageData3:
            image3 = base64_to_image(imageData3, "E://output//upload")
            unit3 = webuiapi.ControlNetUnit(image=image3, module=preprocessor3, model=model_value3,
                                            weight=float(controlWeight3), guidance_start=startTime3,
                                            guidance_end=endTime3, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit3)
    print("controlnet_units:", str(controlnet_units))
    try:
        result = api.txt2img(
            prompt=translated_prompt,
            negative_prompt=translated_negativePrompt,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            batch_size=image_count,
            width=width,
            height=height,
            controlnet_units=controlnet_units,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
        response_data = result.json
        return response_data
    except Exception as e:
        print("error：", e)


def controlNetOrHighRes(high_res_method, controlNets, translated_prompt, translated_negativePrompt, seed, style,
                        cfg_scale, sample, steps, upscale, high_res_steps, width, height, denoise, image_count,
                        sd_model_checkpoint, vae, skip_layers):
    global result
    # 获取并解码 base64 图像
    controlnet_units = []
    unit1 = unit2 = unit3 = None
    if controlNets[0].get('model_value'):
        preprocessor1 = controlNets[0]['preprocessor']
        model_value1 = controlNets[0]['model_value']
        imageData1 = controlNets[0]['image']
        controlWeight1 = controlNets[0]['controlWeight']
        startTime1 = controlNets[0]['startTime']
        endTime1 = controlNets[0]['endTime']
        if imageData1:
            image1 = base64_to_image(imageData1, "E://output//upload")
            unit1 = webuiapi.ControlNetUnit(image=image1, module=preprocessor1, model=model_value1,
                                            weight=float(controlWeight1), guidance_start=startTime1,
                                            guidance_end=endTime1, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit1)

    if controlNets[1].get('model_value'):
        preprocessor2 = controlNets[1]['preprocessor']
        model_value2 = controlNets[1]['model_value']
        imageData2 = controlNets[1]['image']
        controlWeight2 = controlNets[0]['controlWeight']
        startTime2 = controlNets[0]['startTime']
        endTime2 = controlNets[0]['endTime']
        if imageData2:
            image2 = base64_to_image(imageData2, "E://output//upload")
            unit2 = webuiapi.ControlNetUnit(image=image2, module=preprocessor2, model=model_value2,
                                            weight=float(controlWeight2), guidance_start=startTime2,
                                            guidance_end=endTime2, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit2)

    if controlNets[2].get('model_value'):
        preprocessor3 = controlNets[2]['preprocessor']
        model_value3 = controlNets[2]['model_value']
        imageData3 = controlNets[2]['image']
        controlWeight3 = controlNets[0]['controlWeight']
        startTime3 = controlNets[0]['startTime']
        endTime3 = controlNets[0]['endTime']
        if imageData3:
            image3 = base64_to_image(imageData3, "E://output//upload")
            unit3 = webuiapi.ControlNetUnit(image=image3, module=preprocessor3, model=model_value3,
                                            weight=float(controlWeight3), guidance_start=startTime3,
                                            guidance_end=endTime3, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit3)
    print("controlnet_units:", str(controlnet_units))
    if high_res_method == "Latent":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.Latent,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    elif high_res_method == "ESRGAN_4x":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.ESRGAN_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    elif high_res_method == "R-ESRGAN 4x+":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.R_ESRGAN,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    elif high_res_method == "R-ESRGAN 4x+ Anime6B":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.ESRGAN_4x_Anime6B,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    elif high_res_method == "SwinIR_4x":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.SwinIR_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    elif high_res_method == "4x-UltraShar":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.UltraShar_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
        )
    response_data = result.json
    return response_data


def controlNetOrHighResOrAdetailer(aDetailers, high_res_method, controlNets, translated_prompt,
                                   translated_negativePrompt, seed, style, cfg_scale, sample, steps, upscale,
                                   high_res_steps, width, height, denoise, image_count, sd_model_checkpoint, vae,
                                   skip_layers):
    global result
    adetailer_units = []
    for adetailer in aDetailers:
        model = adetailer.get('model')
        if model != "None":
            ads = webuiapi.ADetailer(ad_model=model)
            adetailer_units.append(ads)

    # 获取并解码 base64 图像
    controlnet_units = []
    unit1 = unit2 = unit3 = None
    if controlNets[0].get('model_value'):
        preprocessor1 = controlNets[0]['preprocessor']
        model_value1 = controlNets[0]['model_value']
        imageData1 = controlNets[0]['image']
        controlWeight1 = controlNets[0]['controlWeight']
        startTime1 = controlNets[0]['startTime']
        endTime1 = controlNets[0]['endTime']
        if imageData1:
            image1 = base64_to_image(imageData1, "E://output//upload")
            unit1 = webuiapi.ControlNetUnit(image=image1, module=preprocessor1, model=model_value1,
                                            weight=float(controlWeight1), guidance_start=startTime1,
                                            guidance_end=endTime1, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit1)

    if controlNets[1].get('model_value'):
        preprocessor2 = controlNets[1]['preprocessor']
        model_value2 = controlNets[1]['model_value']
        imageData2 = controlNets[1]['image']
        controlWeight2 = controlNets[0]['controlWeight']
        startTime2 = controlNets[0]['startTime']
        endTime2 = controlNets[0]['endTime']
        if imageData2:
            image2 = base64_to_image(imageData2, "E://output//upload")
            unit2 = webuiapi.ControlNetUnit(image=image2, module=preprocessor2, model=model_value2,
                                            weight=float(controlWeight2), guidance_start=startTime2,
                                            guidance_end=endTime2, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit2)

    if controlNets[2].get('model_value'):
        preprocessor3 = controlNets[2]['preprocessor']
        model_value3 = controlNets[2]['model_value']
        imageData3 = controlNets[2]['image']
        controlWeight3 = controlNets[0]['controlWeight']
        startTime3 = controlNets[0]['startTime']
        endTime3 = controlNets[0]['endTime']
        if imageData3:
            image3 = base64_to_image(imageData3, "E://output//upload")
            unit3 = webuiapi.ControlNetUnit(image=image3, module=preprocessor3, model=model_value3,
                                            weight=float(controlWeight3), guidance_start=startTime3,
                                            guidance_end=endTime3, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit3)
    print("controlnet_units:", str(controlnet_units))
    if high_res_method == "Latent":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.Latent,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )
    elif high_res_method == "ESRGAN_4x":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.ESRGAN_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )
    elif high_res_method == "R-ESRGAN 4x+":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.R_ESRGAN,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )
    elif high_res_method == "R-ESRGAN 4x+ Anime6B":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.ESRGAN_4x_Anime6B,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )
    elif high_res_method == "SwinIR_4x":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.SwinIR_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )
    elif high_res_method == "4x-UltraShar":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            controlnet_units=controlnet_units,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.UltraShar_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )

    response_data = result.json
    return response_data


def HighResOrAdetailer(aDetailers, high_res_method, translated_prompt,
                       translated_negativePrompt, seed, style, cfg_scale, sample, steps, upscale,
                       high_res_steps, width, height, denoise, image_count, sd_model_checkpoint, vae,
                       skip_layers):
    global result
    adetailer_units = []
    for adetailer in aDetailers:
        model = adetailer.get('model')
        if model != "None":
            ads = webuiapi.ADetailer(ad_model=model)
            adetailer_units.append(ads)
    if high_res_method == "Latent":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.Latent,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )
    elif high_res_method == "ESRGAN_4x":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.ESRGAN_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )
    elif high_res_method == "R-ESRGAN 4x+":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.R_ESRGAN,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )
    elif high_res_method == "R-ESRGAN 4x+ Anime6B":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.ESRGAN_4x_Anime6B,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )
    elif high_res_method == "SwinIR_4x":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.SwinIR_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )
    elif high_res_method == "4x-UltraShar":
        result = api.txt2img(
            prompt=translated_prompt,
            # model_info[11]:模型推荐正面tag
            negative_prompt=translated_negativePrompt,
            # model_info[12]:模型推荐负面tag,
            seed=int(seed),
            styles=[style],
            cfg_scale=cfg_scale,
            sampler_index=sample,
            sampler_name=sample,
            steps=steps,
            enable_hr=True,
            hr_scale=upscale,
            hr_upscaler=webuiapi.HiResUpscaler.UltraShar_4x,
            hr_second_pass_steps=high_res_steps,
            hr_resize_x=int(width) * int(upscale),
            hr_resize_y=int(height) * int(upscale),
            denoising_strength=denoise,
            batch_size=image_count,
            width=width,
            height=height,
            override_settings={
                "sd_model_checkpoint": sd_model_checkpoint,
                "sd_vae": vae,
                "CLIP_stop_at_last_layers": int(skip_layers)
            },
            adetailer=adetailer_units
        )

    response_data = result.json
    return response_data


def controlNetOrAdetailer(aDetailers, controlNets, translated_prompt,
                          translated_negativePrompt, seed, style, cfg_scale, sample, steps,
                          width, height, image_count, sd_model_checkpoint, vae,
                          skip_layers):
    global result
    adetailer_units = []
    for adetailer in aDetailers:
        model = adetailer.get('model')
        if model != "None":
            ads = webuiapi.ADetailer(ad_model=model)
            adetailer_units.append(ads)

    # 获取并解码 base64 图像
    controlnet_units = []
    unit1 = unit2 = unit3 = None
    if controlNets[0].get('model_value'):
        preprocessor1 = controlNets[0]['preprocessor']
        model_value1 = controlNets[0]['model_value']
        imageData1 = controlNets[0]['image']
        controlWeight1 = controlNets[0]['controlWeight']
        startTime1 = controlNets[0]['startTime']
        endTime1 = controlNets[0]['endTime']
        if imageData1:
            image1 = base64_to_image(imageData1, "E://output//upload")
            unit1 = webuiapi.ControlNetUnit(image=image1, module=preprocessor1, model=model_value1,
                                            weight=float(controlWeight1), guidance_start=startTime1,
                                            guidance_end=endTime1, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit1)

    if controlNets[1].get('model_value'):
        preprocessor2 = controlNets[1]['preprocessor']
        model_value2 = controlNets[1]['model_value']
        imageData2 = controlNets[1]['image']
        controlWeight2 = controlNets[0]['controlWeight']
        startTime2 = controlNets[0]['startTime']
        endTime2 = controlNets[0]['endTime']
        if imageData2:
            image2 = base64_to_image(imageData2, "E://output//upload")
            unit2 = webuiapi.ControlNetUnit(image=image2, module=preprocessor2, model=model_value2,
                                            weight=float(controlWeight2), guidance_start=startTime2,
                                            guidance_end=endTime2, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit2)

    if controlNets[2].get('model_value'):
        preprocessor3 = controlNets[2]['preprocessor']
        model_value3 = controlNets[2]['model_value']
        imageData3 = controlNets[2]['image']
        controlWeight3 = controlNets[0]['controlWeight']
        startTime3 = controlNets[0]['startTime']
        endTime3 = controlNets[0]['endTime']
        if imageData3:
            image3 = base64_to_image(imageData3, "E://output//upload")
            unit3 = webuiapi.ControlNetUnit(image=image3, module=preprocessor3, model=model_value3,
                                            weight=float(controlWeight3), guidance_start=startTime3,
                                            guidance_end=endTime3, pixel_perfect=True, control_mode=0)
            controlnet_units.append(unit3)
    print("controlnet_units:", str(controlnet_units))
    result = api.txt2img(
        prompt=translated_prompt,
        # model_info[11]:模型推荐正面tag
        negative_prompt=translated_negativePrompt,
        # model_info[12]:模型推荐负面tag,
        seed=int(seed),
        styles=[style],
        cfg_scale=cfg_scale,
        sampler_index=sample,
        sampler_name=sample,
        steps=steps,
        controlnet_units=controlnet_units,
        batch_size=image_count,
        width=width,
        height=height,
        override_settings={
            "sd_model_checkpoint": sd_model_checkpoint,
            "sd_vae": vae,
            "CLIP_stop_at_last_layers": int(skip_layers)
        },
        adetailer=adetailer_units
    )
    response_data = result.json
    return response_data