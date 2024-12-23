import asyncio, streamlink, subprocess, os, configparser
from datetime import datetime
from tkinter import filedialog, Tk
from time import sleep as s


config_file_path = 'config.ini'
config = configparser.ConfigParser()

# Check if the config file exists, if not create one
if not os.path.exists(config_file_path):
    config['DEFAULT'] = {'output_folder': ''}
    with open(config_file_path, 'w') as configfile:
        config.write(configfile)

# Load the config file
config.read(config_file_path)
twitch_username = input('Streamer Username to record: ')
output_folder = config['DEFAULT']['output_folder']

# If the output_folder variable is not set, ask the user for input and open file explorer
if not output_folder:
    print('\nNow please choose the Folder location, in which all future recordings should be saved into.\nA explorer window should open up soon ...')
    s(3)
    root = Tk()
    root.withdraw()
    output_folder = filedialog.askdirectory(title="Select Output Folder")
    config['DEFAULT']['output_folder'] = output_folder
    root.destroy()

# Save the variables to the config file
with open(config_file_path, 'w') as configfile:
    config.write(configfile)

os.system(f"title {twitch_username} @ {output_folder}")

async def get_best_stream_url(username):
    # Construct the Twitch stream URL using the username
    twitch_stream_url = f"https://www.twitch.tv/{username}"

    # Use streamlink to retrieve the available streams for the Twitch stream URL
    streams = streamlink.streams(twitch_stream_url)

    # Check if the 'best' stream is available and get its .m3u8 URL
    if 'best' in streams:
        best_stream = streams['best']
        m3u8_url = best_stream.url
        print(f"Will record from best livestream .m3u8 URL: {m3u8_url}")
        return m3u8_url
    else:
        print("No available streams found.")

async def record_stream(username):
    m3u8_url = await get_best_stream_url(username)
    if m3u8_url:
        # Use a transport stream format (.ts) for resilient recording
        ts_file = os.path.join(output_folder, f"{twitch_username}_{datetime.now().strftime('%d_%m_%y_%H_%M')}.ts")
        
        # Run ffmpeg command
        ffmpeg_cmd = [
            'ffmpeg', '-i', m3u8_url,
            '-c', 'copy', '-f', 'mpegts', ts_file
        ]
        
        print(f"Starting recording: {ts_file}")
        process = await asyncio.create_subprocess_exec(*ffmpeg_cmd)
        await process.communicate()
        
        print(f"Recording complete: {ts_file}")
        
        # Optional: Convert .ts to .mp4
        mp4_file = ts_file.replace('.ts', '.mp4')
        ffmpeg_convert_cmd = [
            'ffmpeg', '-i', ts_file, '-c', 'copy', mp4_file
        ]
        print(f"Converting to MP4: {mp4_file}")
        convert_process = await asyncio.create_subprocess_exec(*ffmpeg_convert_cmd)
        await convert_process.communicate()
        
        print(f"Conversion complete: {mp4_file}")
        os.remove(ts_file)  # Remove the intermediate .ts file if conversion succeeds

if __name__ == '__main__':
    asyncio.run(record_stream(twitch_username))
