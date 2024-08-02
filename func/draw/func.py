import base64
import io
import os
import random
import string
from PIL import Image

import webuiapi

api = webuiapi.WebUIApi(host='127.0.0.1', port=7860)
api.set_auth('panllq', 'Pan.960327')


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