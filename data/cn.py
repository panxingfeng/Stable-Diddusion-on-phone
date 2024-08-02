from collections import defaultdict

preprocessor_data = defaultdict(list, {
    'ip-adapter': ['none', 'ip-adapter-auto', 'ip-adapter_clip_h', 'ip-adapter_pulid', 'ip-adapter_face_id_plus',
                   'ip-adapter_face_id', 'ip-adapter_clip_sdxl_plus_vith', 'ip-adapter_clip_g'],
    'revision': ['none', 'revision_clipvision', 'revision_ignore_prompt'],
    'reference': ['none', 'reference_only', 'reference_adain+attn', 'reference_adain'],
    'recolor': ['none', 'recolor_luminance', 'recolor_intensity'],
    'openpose': ['openpose_full', 'openpose_hand', 'openpose_faceonly', 'openpose_face', 'openpose',
                 'dw_openpose_full'],
    'normalmap': ['none', 'normal_bae', 'normal_midas'],
    'mlsd': ['none', 'mlsd', 'invert'],
    'lineart': ['None', 'lineart_standard', 'invert', 'lineart_realistic', 'lineart_coarse', 'lineart_anime_denoise',
                'lineart_anime'],
    'inpaint': ['inpaint_only', 'inpaint_only+lama', 'inpaint'],
    'depth': ['none', 'depth_midas', 'depth_zoe', 'depth_leres++', 'depth_leres'],
    'canny': ['none', 'canny', 'invert'],
    'tile': ['none', 'tile_resample', 'tile_colorfix+sharp', 'tile_colorfix', 'blur_gaussian'],
    't2i-adapter': ['none', 't2ia_style_clipvision', 't2ia_sketch_pidi', 't2ia_color_grid'],
    'softedge': ['none', 'softedge_pidinet', 'softedge_teed', 'softedge_pidisafe', 'softedge_hedsafe', 'softedge_hed',
                 'softedge_anyline'],
    'shuffle': ['none', 'shuffle'],
    'segmentation': ['none', 'seg_ofade20k', 'seg_ufade20k', 'seg_ofcoco', 'seg_anime_face'],
    'scribble': ['none', 'scribble_pidinet', 'scribble_xdog', 'scribble_hed', 'invert'],
    'instant-id': ['none'],
    'sparsectrl': ['none', 'scribble_pidinet', 'scribble_xdog', 'scribble_hed', 'invert'],
    'instructp2p': ['none'],
    "else": ["none"]
})

# 模型数据
model_data = defaultdict(list, {
    'ip-adapter': ['None', 'ip-adapter-faceid-plus_sd15 [d86a490f]', 'ip-adapter-faceid-plusv2_sd15 [6e14fc1a]',
                   'ip-adapter-faceid-portrait_sd15 [b2609049]',
                   'ip-adapter [eb2d3ec0]', 'ip-adapter_sd15 [6a3f6166]', 'ip-adapter_sd15_plus [32cd8f7f]'],
    'recolor': ['None', 'ioclab_sd15_recolor [6641f3c6]'],
    'openpose': ['None', 'control_v11p_sd15_openpose [cab727d4]'],
    'normalmap': ['None', 'control_v11p_sd15_normalbae [316696f1]'],
    'mlsd': ['None', 'control_v11p_sd15_mlsd [aca30ff0]', 'control_v11p_sd15_mlsd_fp16 [77b5ad24]'],
    'lineart': ['None', 'control_v11p_sd15_lineart [43d4be0d]', 'control_v11p_sd15s2_lineart_anime [3825e83e]'],
    'inpaint': ['inpaint_only_model', 'inpaint_only+lama_model', 'inpaint_model'],
    'depth': ['None',
              'control_v11f1p_sd15_depth [cfd03158]'],
    'canny': ['None', 'control_v11p_sd15_canny [d14c016b]', 't2iadapter_canny_sd15v2 [cecee02b]'],
    'tile': ['None', 'control_v11f1e_sd15_tile [a371b31b]'],
    't2i-adapter': ['None', 't2iadapter_canny_sd15v2 [cecee02b]', 't2iadapter_color_sd14v1 [8522029d]',
                    't2iadapter_sketch_sd14v1 [e5d4b846]', 't2iadapter_style_sd14v1 [202e85cc]'],
    'softedge': ['None', 'control_v11p_sd15_softedge [a8575a2a]', 'control_v11p_sd15_softedge_fp16 [f616a34f]'],
    'shuffle': ['None', 'control_v11e_sd15_shuffle [526bfdae]'],
    'segmentation': ['None', 'control_v11p_sd15_seg [e1f51eb9]'],
    'scribble': ['None', 'control_v11p_sd15_scribble [d4ba51ff]', 't2iadapter_sketch_sd14v1 [e5d4b846]'],
    'instant-id': ['control_instant_id_sdxl [c5c25a50]'],
    'sparsectrl': ['None'],
    'instructp2p': ['None', 'control_v11e_sd15_ip2p [c4bb465c]'],
    'else': ['control_v1p_sd15_qrcode_monster [a6e58995]', 'control_v1p_sd15_qrcode_monster_v2 [5e5778cb]',
             'lightingBasedPicture_v10 [0c4bd571]', 'control_v1p_sd15_brightness [5f6aa6ed]']
})