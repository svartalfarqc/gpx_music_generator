import gpxpy
import mido
from mido import MidiFile, MidiTrack, Message
from geopy.distance import geodesic
from tkinter import Tk, Label, Button, filedialog, Entry, Scale

def calculate_rolling_average_speed(points, window_size):
    rolling_speeds = []
    
    for i in range(len(points) - window_size + 1):
        window_points = points[i:i+window_size]
        total_distance = sum(geodesic((p1.latitude, p1.longitude), (p2.latitude, p2.longitude)).meters
                             for p1, p2 in zip(window_points[:-1], window_points[1:]))
        
        total_time = (window_points[-1].time - window_points[0].time).total_seconds()
        average_speed = total_distance / total_time if total_time > 0 else 0
        
        rolling_speeds.append(average_speed)
    
    return rolling_speeds

def gpx_to_midi(gpx_filename, min_note, max_note, window_size, tempo):
    # Load GPX file
    with open(gpx_filename, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Create MIDI file
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)

    # Set initial parameters
    ticks_per_beat = 480
    tempo = int(60000000 / tempo)  # microseconds per beat
    track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))

    # Extract data from GPX and generate MIDI notes
    total_distance = 0
    total_time = 0
    elevation_data = [point.elevation for point in gpx.tracks[0].segments[0].points]
    elevation_range = max(elevation_data) - min(elevation_data)
    min_elevation = min(elevation_data)
    rolling_speeds = calculate_rolling_average_speed(gpx.tracks[0].segments[0].points, window_size)
    
    for i in range(len(gpx.tracks[0].segments[0].points) - window_size):
        point1 = gpx.tracks[0].segments[0].points[i]
        point2 = gpx.tracks[0].segments[0].points[i + window_size]

        distance = geodesic((point1.latitude, point1.longitude), (point2.latitude, point2.longitude)).meters
        total_distance += distance

        time_difference = (point2.time - point1.time).total_seconds()
        total_time += time_difference

        # Calculate average rolling speed and map it to MIDI note velocity
        speed = rolling_speeds[i]
        velocity = 100  # Set a fixed velocity value (e.g., 100)

        # Map altitude to MIDI note within the specified range
        altitude_note = int((point1.elevation - min_elevation) / elevation_range * (max_note - min_note) + min_note)

        # Map speed to note duration (inverse relationship)
        note_duration = int(1 / speed * ticks_per_beat) if speed > 0 else 0

        # Add note-on and note-off messages to the MIDI track
        track.append(Message('note_on', note=altitude_note, velocity=velocity, time=0))
        track.append(Message('note_off', note=altitude_note, velocity=velocity, time=note_duration))

    return midi

def save_midi_file(min_note, max_note, window_size, tempo):
    global output_filename_entry
    gpx_filename = filedialog.askopenfilename(filetypes=[("GPX files", "*.gpx")])
    if gpx_filename:
        save_path = filedialog.asksaveasfilename(defaultextension=".mid", filetypes=[("MIDI files", "*.mid")], initialfile="output.mid")
        if save_path:
            midi_file = gpx_to_midi(gpx_filename, min_note, max_note, window_size, tempo)
            midi_file.save(save_path)
            status_label.config(text=f"MIDI file saved: {save_path}")

# Create Tkinter window
root = Tk()
root.title("GPX to MIDI Converter")

# Create and place UI elements
min_note_label = Label(root, text="Min Note:")
min_note_label.pack()

min_note_scale = Scale(root, from_=0, to=127, orient="horizontal")
min_note_scale.set(0)
min_note_scale.pack()

max_note_label = Label(root, text="Max Note:")
max_note_label.pack()

max_note_scale = Scale(root, from_=0, to=127, orient="horizontal")
max_note_scale.set(127)
max_note_scale.pack()

window_size_label = Label(root, text="Rolling Speed Window Size:")
window_size_label.pack()

window_size_scale = Scale(root, from_=1, to=50, orient="horizontal")
window_size_scale.set(5)
window_size_scale.pack()

tempo_label = Label(root, text="Tempo (BPM):")
tempo_label.pack()

tempo_scale = Scale(root, from_=1, to=300, orient="horizontal")
tempo_scale.set(120)
tempo_scale.pack()

select_button = Button(root, text="Select GPX File", command=lambda: save_midi_file(min_note_scale.get(), max_note_scale.get(), window_size_scale.get(), tempo_scale.get()))
select_button.pack(pady=20)

status_label = Label(root, text="")
status_label.pack()

# Run the Tkinter event loop
root.mainloop()
