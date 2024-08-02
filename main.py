import json
import subprocess
import uuid

import pymysql
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from threading import Thread
from data.cn import *
from func.database.azure.func import upload_to_azure
from func.database.mysql.func import handle_request, create_connection, get_db_connection
from func.draw.func import *

app = Flask(__name__, static_folder='static')
CORS(app)  # 启用 CORS 支持

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)

# 存储用户对话历史的字典
user_histories = {}

# 最大历史记录长度
MAX_USER_HISTORY_LENGTH = 5
MAX_ASSISTANT_HISTORY_LENGTH = 5

@app.route('/add_task', methods=['POST'])
def add_task():
    task_data = request.json.get('data')
    print("task_data:", task_data)
    task_id = str(time.time())  # 使用时间戳作为任务ID
    task_queue.put((task_id, task_data))
    tasks_in_progress[task_id] = {'status': 'queued', 'progress': 0.0}
    task_id_list.append(task_id)
    print(f"Added task {task_id}")
    return jsonify({'task_id': task_id, 'status': 'queued'})


@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    task_info = tasks_in_progress.get(task_id, {'status': 'not found'})
    queue_position = task_id_list.index(task_id) + 1 if task_info['status'] == 'queued' else 0
    tasks_in_progress_count = len([task for task in tasks_in_progress.values() if task['status'] == 'in progress'])

    # 初始化进度为0.0
    progress = 0.0

    # 只有在任务状态为 in progress 时才请求进度数据
    if task_info['status'] == 'in progress':
        try:
            progress_response = requests.get(f'{API_URL}/sdapi/v1/progress', headers=HEADERS)
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                progress = progress_data.get('progress', 0.0)
        except requests.RequestException as e:
            print(f"Error fetching progress: {e}")
            progress = 0.0

    return jsonify({
        'task_id': task_id,
        'status': task_info['status'],
        'progress': progress,
        'queue_position': queue_position,
        'tasks_in_progress': tasks_in_progress_count,
        'images': task_info.get('images', []),
        'info_texts': task_info.get('info_texts', []),
        'seed': task_info.get('seed'),
        'task_data': task_info.get('task_data', {}),
    })


@app.route('/generate_images', methods=['POST'])
def generate_images():
    global result1, result, azure_url
    task_data = request.json
    print("task_data:", task_data)
    prompt = task_data['prompt']
    sd_model_checkpoint = task_data.get("sd_model_checkpoint")
    aDetailers = task_data.get('adetailer')
    adetailerEnabled = task_data.get('adetailerEnabled')
    cfg_scale = task_data.get('cfg_scale')
    width = task_data.get('width')
    height = task_data.get('height')
    image_count = task_data.get('image_count')
    steps = task_data.get('steps')
    high_res_method = task_data.get('high_res_method')
    upscale = task_data.get('upscale')
    denoise = task_data.get('denoise')
    high_res_steps = task_data.get('high_res_steps')
    skip_layers = task_data.get('skip_layers')
    sample = str(task_data.get('sample'))
    style = str(task_data.get('style'))
    vae = task_data.get('vae')
    controlNet = task_data.get('controlNet')
    controlNets = task_data.get('controlNets')

    if not task_data['negative_prompt']:
        negative_prompt = "none"
    else:
        negative_prompt = task_data['negative_prompt']

    if not task_data['seed']:
        seed = -1
    else:
        seed = task_data['seed']

    if high_res_method != "":
        if str(controlNet) == "True":
            if str(adetailerEnabled) == "True":
                print("来三者归一这啦")
                response_data = controlNetOrHighResOrAdetailer(aDetailers, high_res_method, controlNets,
                                                               prompt,
                                                               negative_prompt, seed, style, cfg_scale,
                                                               sample, steps,
                                                               upscale, high_res_steps, width, height, denoise,
                                                               image_count,
                                                               sd_model_checkpoint, vae, skip_layers)
            else:
                print("来控制网和高分辨这啦")
                response_data = controlNetOrHighRes(high_res_method, controlNets, prompt,
                                                    negative_prompt,
                                                    seed, style, cfg_scale, sample, steps, upscale, high_res_steps,
                                                    width,
                                                    height, denoise, image_count, sd_model_checkpoint, vae, skip_layers)
        elif str(adetailerEnabled) == "True":
            if str(controlNet) == "True":
                print("来三者归一这啦")
                response_data = controlNetOrHighResOrAdetailer(aDetailers, high_res_method, controlNets,
                                                               prompt,
                                                               negative_prompt, seed, style, cfg_scale,
                                                               sample, steps,
                                                               upscale, high_res_steps, width, height, denoise,
                                                               image_count,
                                                               sd_model_checkpoint, vae, skip_layers)
            else:
                print("来高分辨和修复这啦")
                response_data = HighResOrAdetailer(aDetailers, high_res_method, prompt,
                                                   negative_prompt, seed, style, cfg_scale, sample, steps,
                                                   upscale,
                                                   high_res_steps, width, height, denoise, image_count,
                                                   sd_model_checkpoint,
                                                   vae,
                                                   skip_layers)
        else:
            print("来高分辨这啦")
            response_data = high_res(high_res_method, prompt, negative_prompt, seed, style,
                                     cfg_scale,
                                     sample, steps,
                                     upscale, high_res_steps, width, height, denoise, image_count, sd_model_checkpoint,
                                     vae,
                                     skip_layers)
    elif str(controlNet) == "True":
        if high_res_method != "":
            if str(adetailerEnabled) == "True":
                print("来三者归一这啦")
                response_data = controlNetOrHighResOrAdetailer(aDetailers, high_res_method, controlNets,
                                                               prompt,
                                                               negative_prompt, seed, style, cfg_scale,
                                                               sample, steps,
                                                               upscale, high_res_steps, width, height, denoise,
                                                               image_count,
                                                               sd_model_checkpoint, vae, skip_layers)
            else:
                print("来控制网和高分辨这啦")
                response_data = controlNetOrHighRes(high_res_method, controlNets, prompt,
                                                    negative_prompt,
                                                    seed, style, cfg_scale, sample, steps, upscale, high_res_steps,
                                                    width,
                                                    height, denoise, image_count, sd_model_checkpoint, vae, skip_layers)
        elif str(adetailerEnabled) == "True":
            if high_res_method != "":
                print("来三者归一这啦")
                response_data = controlNetOrHighResOrAdetailer(aDetailers, high_res_method, controlNets,
                                                               prompt,
                                                               negative_prompt, seed, style, cfg_scale,
                                                               sample, steps,
                                                               upscale, high_res_steps, width, height, denoise,
                                                               image_count,
                                                               sd_model_checkpoint, vae, skip_layers)
            else:
                print("来控制网和修复这啦")
                response_data = controlNetOrAdetailer(aDetailers, controlNets, prompt,
                                                      negative_prompt, seed, style, cfg_scale, sample, steps,
                                                      width, height, image_count, sd_model_checkpoint, vae,
                                                      skip_layers)
        else:
            print("来控制网这啦")
            response_data = controlNetMethod(controlNets, prompt, negative_prompt, seed, style,
                                             cfg_scale, sample, steps, width, height, image_count, sd_model_checkpoint,
                                             vae,
                                             skip_layers)
    elif str(adetailerEnabled) == "True":
        if high_res_method != "":
            if str(controlNet) == "True":
                print("来三者归一这啦")
                response_data = controlNetOrHighResOrAdetailer(aDetailers, high_res_method, controlNets,
                                                               prompt,
                                                               negative_prompt, seed, style, cfg_scale,
                                                               sample, steps,
                                                               upscale, high_res_steps, width, height, denoise,
                                                               image_count,
                                                               sd_model_checkpoint, vae, skip_layers)
            else:
                print("来高分辨和修复这啦")
                response_data = HighResOrAdetailer(aDetailers, high_res_method, prompt,
                                                   negative_prompt, seed, style, cfg_scale, sample, steps,
                                                   upscale,
                                                   high_res_steps, width, height, denoise, image_count,
                                                   sd_model_checkpoint,
                                                   vae,
                                                   skip_layers)
        elif str(controlNet) == "True":
            if high_res_method != "":
                print("来三者归一这啦")
                response_data = controlNetOrHighResOrAdetailer(aDetailers, high_res_method, controlNets,
                                                               prompt,
                                                               negative_prompt, seed, style, cfg_scale,
                                                               sample, steps,
                                                               upscale, high_res_steps, width, height, denoise,
                                                               image_count,
                                                               sd_model_checkpoint, vae, skip_layers)
            else:
                print("来控制网和修复这啦")
                response_data = controlNetOrAdetailer(aDetailers, controlNets, prompt,
                                                      negative_prompt, seed, style, cfg_scale, sample, steps,
                                                      width, height, image_count, sd_model_checkpoint, vae,
                                                      skip_layers)
        else:
            print("来修复这啦")
            response_data = aDetailerMethod(aDetailers, prompt, negative_prompt, seed, style,
                                            cfg_scale,
                                            sample, steps,
                                            width, height, image_count, sd_model_checkpoint, vae, skip_layers)

    else:
        print("任务好轻，没有挑战性")
        response_data = moRen(prompt, negative_prompt, seed, style, cfg_scale, sample, steps,
                              width, height, image_count, sd_model_checkpoint, vae, skip_layers)

    # 检查响应数据并获取图像列表
    if isinstance(response_data, dict) and "images" in response_data:
        base64_data_list = response_data.get("images")
        info = response_data.get("info")
        info_data = json.loads(info)
        info_texts = info_data.get("infotexts", [])

        if isinstance(base64_data_list, list) and len(base64_data_list) > 0:
            output_dir = "E:/output/pages_save"
            os.makedirs(output_dir, exist_ok=True)
            saved_files = []

            # 保存每个图像和对应的info_texts
            for i, base64_data in enumerate(base64_data_list):
                img_data = base64.b64decode(base64_data)
                img = Image.open(io.BytesIO(img_data))
                filename = generate_random_filename()
                img_file_path = os.path.join(output_dir, f"{filename}.png")
                txt_file_path = os.path.join(output_dir, f"{filename}.txt")

                azure_url = upload_to_azure(img_file_path, filename + ".png", 1)

                # 保存图像
                img.save(img_file_path)
                saved_files.append(img_file_path)

                # 检查info_texts的长度
                if i < len(info_texts):
                    info_text = info_texts[i]
                else:
                    info_text = "No info available."

                # 保存info_texts到对应的txt文件
                with open(txt_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"prompt:{info_text}")

            return jsonify({'images': base64_data_list, 'info_texts': info_texts, 'azure_url': azure_url})
        else:
            return jsonify(
                {'error': "The 'images' key should contain a list with at least one base64 string."}), 400
    else:
        return jsonify({'error': "The response data is not in the expected format."}), 400


@app.route('/api/lora_folders_and_models', methods=['GET'])
def get_lora_folders_and_models():
    return handle_request('lora', r'D:\BaiduNetdiskDownload\sd-webui-aki-v4.8\models\Lora')


@app.route('/api/embedding_folders_and_models', methods=['GET'])
def get_embedding_folders_and_models():
    return handle_request('embedding', r'D:\BaiduNetdiskDownload\sd-webui-aki-v4.8\embeddings')


@app.route('/api/model_folders_and_models', methods=['GET'])
def get_model_folders_and_models():
    return handle_request('model', r'D:\BaiduNetdiskDownload\sd-webui-aki-v4.8\models\Stable-diffusion')


@app.route('/process-data', methods=['POST'])
def process_data():
    global content_role
    data = request.get_json()
    user_input = data.get('input')
    model_name = data.get('model')
    if model_name == "anything":
        model_name = "ollama模型"
        content_role = "你是由PanllQ创作，是一个专注于帮助用户完成AI精美图像描述词的智能提示词助手，根据用户输入的内容作为主题内容，提示词中增加更多丰富的内容，使得画面内容更加的丰富，输出内容只包含提示词内容，内容一句话即可，拒绝黄色暴力等限制级内容的生成，回复的格式：英文，这是用户的内容："
    url = 'http://localhost:11434/api/chat'
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    data = {
        "model": model_name,
        "messages": [
            {"role": "user",
             "content": content_role + user_input}
        ],
        "stream": False
    }

    command = f'ollama run {model_name}'
    subprocess.Popen(['powershell', '-command', command], shell=True)
    response = requests.post(url, json=data, headers=headers)

    chat_message = response.json()['message']['content']
    if model_name == "llama3":
        matches = re.findall(r'"(.*?)"', chat_message, re.S)
        if matches:
            extracted_content = matches[1]  # 这里选择第二个匹配项，即引号内的内容
            return jsonify({'reply': extracted_content})
    return jsonify({'reply': chat_message})

@app.route('/controlNet/optionValue', methods=['POST'])
def get_option_value():
    options_data = api.controlnet_module_list()
    data = request.json
    control_type = data.get('controlType')
    options = options_data.get(control_type, options_data['none'])

    return jsonify(options)


@app.route('/controlNet/options', methods=['POST'])
def get_controlnet_options():
    try:
        data = request.json
        app.logger.info(f"Received data: {data}")
        control_type = data.get('controlType')

        if not control_type:
            app.logger.error("controlType is required")
            return jsonify({'error': 'controlType is required'}), 400

        preprocessor_options = preprocessor_data.get(control_type.lower(), preprocessor_data['none'])
        app.logger.info(f"Preprocessor options for {control_type}: {preprocessor_options}")

        model_options = model_data.get(control_type.lower(), [])
        app.logger.info(f"Model options for {control_type}: {model_options}")

        response_data = {
            'preprocessorOptions': [{'value': opt, 'text': opt.replace('_', ' ').title()} for opt in
                                    preprocessor_options],
            'modelOptions': [{'value': model, 'text': model.replace('_', ' ').title()} for model in model_options]
        }

        app.logger.info(f"Response data: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error occurred: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/queue_status', methods=['GET'])
def queue_status():
    position = 0
    task_id = request.args.get('task_id')

    if task_id:
        for idx, (tid, _) in enumerate(list(task_queue.queue)):
            if tid == task_id:
                position = idx + 1
                break

    return jsonify({
        'queue_length': task_queue.qsize(),
        'current_tasks': 1 if current_task_id else 0,
        'position': position
    })

@app.route('/clear-history/<user_id>', methods=['DELETE'])
def clear_history(user_id):
    if user_id in user_histories:
        del user_histories[user_id]
    return '', 204

@app.route('/process-image-inversion', methods=['POST'])
def process_image_inversion():
    data = request.json
    base64_image = data.get('image')

    if not base64_image:
        return jsonify({"error": "No image provided"}), 400

    image_data = base64.b64decode(base64_image)
    unique_filename = str(uuid.uuid4()) + '.png'
    image_path = os.path.join(f"E://output//use_upload//{unique_filename}")
    print(image_path)
    with open(image_path, 'wb') as file:
        file.write(image_data)

    result = generate_image_from_image(image_path)
    print("result" + str(result))
    return jsonify(result), 200


@app.route('/folders', methods=['GET'])
def get_main_folders():
    conn = create_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT DISTINCT folder FROM image_paths")
    folders = cursor.fetchall()
    conn.close()
    return jsonify({"folders": folders})


@app.route('/subfolders/<main_folder>', methods=['GET'])
def get_sub_folders(main_folder):
    conn = create_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT DISTINCT subfolder FROM image_paths WHERE folder=%s", (main_folder,))
    sub_folders = cursor.fetchall()
    conn.close()
    return jsonify({"subFolders": sub_folders})


@app.route('/upload_folder', methods=['GET'])
@app.route('/upload_folder/<path:folder_path>', methods=['GET'])
def stream_images(folder_path=''):
    conn = create_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    if folder_path:
        parts = folder_path.split('/')
        if len(parts) == 1:
            cursor.execute("SELECT id, url FROM image_paths WHERE folder=%s", (folder_path,))
        elif len(parts) == 2:
            cursor.execute("SELECT id, url FROM image_paths WHERE folder=%s AND subfolder=%s", (parts[0], parts[1]))
    else:
        cursor.execute("SELECT id, url FROM image_paths")
    images = cursor.fetchall()
    conn.close()

    def generate():
        for image in images:
            yield f"data: {json.dumps({'id': image['id'], 'url': image['url']})}\n\n"
        yield "data: [END_OF_URLS]\n\n"

    return Response(generate(), content_type='text/event-stream')


@app.route('/image_info/<int:image_id>', methods=['GET'])
def get_image_info(image_id):
    conn = create_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM image_info WHERE id=%s", (image_id,))
    image_info = cursor.fetchone()
    conn.close()
    if image_info is None:
        return jsonify({'error': 'Image not found'}), 404

    return jsonify(image_info)

@app.route('/main_categories', methods=['GET'])
def get_all_main_categories():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name FROM main_categories")
    main_categories = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(main_categories)

@app.route('/sub_categories', methods=['GET'])
def get_all_sub_categories():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, main_category_id FROM sub_categories")
    sub_categories = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(sub_categories)

@app.route('/prompts/<int:sub_category_id>', methods=['GET'])
def get_prompts(sub_category_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT cn, en FROM prompts WHERE sub_category_id = %s", (sub_category_id,))
    prompts = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(prompts)


worker_thread = Thread(target=check_progress, daemon=True)
worker_thread.start()


@app.route('/', methods=['GET'])
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/prompt', methods=['GET'])
def prompts():
    return send_from_directory(app.static_folder, 'prompt.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8081)
