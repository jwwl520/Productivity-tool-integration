"""
调试字幕偏移逻辑
模拟当前代码的执行流程
"""

def simulate_current_logic():
    """模拟当前代码逻辑"""
    print("=" * 70)
    print("模拟当前代码逻辑")
    print("=" * 70)
    
    # 模拟数据：3个视频，每个1000帧，30fps
    videos = [
        {"name": "EP01.mp4", "frames": 1000, "fps": 30.0, "has_subtitle": True},
        {"name": "EP02.mp4", "frames": 1000, "fps": 30.0, "has_subtitle": True},
        {"name": "EP03.mp4", "frames": 1000, "fps": 30.0, "has_subtitle": False},  # 缺少字幕
        {"name": "EP04.mp4", "frames": 1000, "fps": 30.0, "has_subtitle": True},
    ]
    
    cumulative_frames = 0
    reference_fps = None
    processed_count = 0
    
    for i, video in enumerate(videos):
        video_name = video["name"]
        video_frames = video["frames"]
        video_fps = video["fps"]
        has_subtitle = video["has_subtitle"]
        
        # 设置参考帧率
        if reference_fps is None and video_fps > 0:
            reference_fps = video_fps
            print(f"\n使用参考帧率: {reference_fps} fps")
        
        print(f"\n--- 处理视频 {i+1}: {video_name} ---")
        print(f"  视频帧数: {video_frames}")
        print(f"  当前累积帧数: {cumulative_frames}")
        
        # 检查是否有字幕
        if not has_subtitle:
            print(f"  ⚠️ 警告：未找到字幕文件，跳过")
            # 即使跳过字幕，也要累加帧数
            if video_frames > 0:
                cumulative_frames += video_frames
                print(f"  累积帧数（跳过后）: {cumulative_frames}")
            continue
        
        # 计算偏移量（显示用）
        if reference_fps and reference_fps > 0:
            current_offset_seconds = cumulative_frames / reference_fps
            print(f"  偏移量: {current_offset_seconds:.3f}秒")
        
        # 应用偏移
        if reference_fps and reference_fps > 0 and cumulative_frames > 0:
            offset_ms = int((cumulative_frames * 1000.0) / reference_fps)
            print(f"  ✅ 应用偏移: {offset_ms}毫秒")
        elif cumulative_frames == 0:
            print(f"  ✅ 首个视频，无需偏移")
        else:
            print(f"  ❌ 缺少帧率信息，跳过偏移")
        
        # 累加帧数
        if video_frames > 0:
            cumulative_frames += video_frames
            print(f"  累积帧数（处理后）: {cumulative_frames}")
        
        processed_count += 1
    
    print(f"\n{'='*70}")
    print(f"处理完成！共处理 {processed_count} 个字幕")
    print(f"最终累积帧数: {cumulative_frames}")
    print(f"{'='*70}\n")


def simulate_correct_logic():
    """模拟修正后的正确逻辑"""
    print("=" * 70)
    print("模拟修正后的正确逻辑（预期行为）")
    print("=" * 70)
    
    videos = [
        {"name": "EP01.mp4", "frames": 1000, "fps": 30.0, "has_subtitle": True},
        {"name": "EP02.mp4", "frames": 1000, "fps": 30.0, "has_subtitle": True},
        {"name": "EP03.mp4", "frames": 1000, "fps": 30.0, "has_subtitle": False},
        {"name": "EP04.mp4", "frames": 1000, "fps": 30.0, "has_subtitle": True},
    ]
    
    cumulative_frames = 0
    reference_fps = None
    processed_count = 0
    
    for i, video in enumerate(videos):
        video_name = video["name"]
        video_frames = video["frames"]
        video_fps = video["fps"]
        has_subtitle = video["has_subtitle"]
        
        if reference_fps is None and video_fps > 0:
            reference_fps = video_fps
            print(f"\n使用参考帧率: {reference_fps} fps")
        
        print(f"\n--- 处理视频 {i+1}: {video_name} ---")
        print(f"  视频帧数: {video_frames}")
        print(f"  当前累积帧数（处理前）: {cumulative_frames}")
        
        if not has_subtitle:
            print(f"  ⚠️ 警告：未找到字幕文件，跳过字幕处理")
            # 关键：即使跳过字幕，也必须累加帧数！
            cumulative_frames += video_frames
            print(f"  累积帧数（跳过后）: {cumulative_frames}")
            continue
        
        # 计算并显示偏移
        if reference_fps and reference_fps > 0:
            current_offset_seconds = cumulative_frames / reference_fps
            offset_ms = int((cumulative_frames * 1000.0) / reference_fps)
            print(f"  偏移量: {current_offset_seconds:.3f}秒 ({offset_ms}毫秒)")
            
            if cumulative_frames > 0:
                print(f"  ✅ 应用偏移: {offset_ms}毫秒")
            else:
                print(f"  ✅ 首个视频，无需偏移（0毫秒）")
        
        # 累加当前视频的帧数（处理完字幕后）
        cumulative_frames += video_frames
        print(f"  累积帧数（处理后）: {cumulative_frames}")
        
        processed_count += 1
    
    print(f"\n{'='*70}")
    print(f"处理完成！共处理 {processed_count} 个字幕")
    print(f"最终累积帧数: {cumulative_frames}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    simulate_current_logic()
    print("\n\n")
    simulate_correct_logic()
    
    print("\n" + "="*70)
    print("对比分析：")
    print("="*70)
    print("""
当前代码的问题：
1. EP01: cumulative=0, 不偏移 ✓, 累加后=1000 ✓
2. EP02: cumulative=1000, 偏移1000帧 ✓, 累加后=2000 ✓
3. EP03: cumulative=2000, 跳过字幕, 累加后=3000 ✓
4. EP04: cumulative=3000, 偏移3000帧 ✓, 累加后=4000 ✓

看起来逻辑是正确的！

可能的问题：
1. 视频扫描时帧数为0？
2. reference_fps未正确设置？
3. 条件判断有遗漏？

需要查看实际运行日志来确定问题！
""")
