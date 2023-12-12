import gpxpy
import mido
from mido import MidiFile, MidiTrack, Message
from geopy.distance import geodesic
from tkinter import Tk, Label, Button, filedialog, Entry, Scale

def gpx_to_midi(gpx_filename, min_note, max_note):
    # Load GPX file
    with open(gpx_filename, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Create MIDI file
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)

    # Set initial parameters
    ticks_per_beat = 480
    tempo = int(60000000 / 120)  # microseconds per beat (bpm = 120)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))

    # Extract data from GPX and generate MIDI notes
    total_distance = 0
    total_time = 0
    for track_segment in gpx.tracks[0].segments:
        for i in range(len(track_segment.points) - 1):
            point1 = track_segment.points[i]
            point2 = track_segment.points[i + 1]

            distance = geodesic((point1.latitude, point1.longitude), (point2.latitude, point2.longitude)).meters
            total_distance += distance

            time_difference = (point2.time - point1.time).total_seconds()
            total_time += time_difference

            # Calculate speed (distance/time) and map it to MIDI note velocity
            speed = distance / time_difference
            velocity = 100  # Set a fixed velocity value (e.g., 100)

            # Map altitude to MIDI note within the specified range
            altitude_note = int((point1.elevation - min_note) / (max_note - min_note) * 128) % 128

            # Map speed to note duration (inverse relationship)
            note_duration = int(1 / speed * ticks_per_beat) if speed > 0 else 0

            # Add note-on and note-off messages to the MIDI track
            track.append(Message('note_on', note=altitude_note, velocity=velocity, time=0))
            track.append(Message('note_off', note=altitude_note, velocity=velocity, time=note_duration))

    return midi

def save_midi_file(min_note, max_note):
    global output_filename_entry
    gpx_filename = filedialog.askopenfilename(filetypes=[("GPX files", "*.gpx")])
    if gpx_filename:
        save_path = filedialog.asksaveasfilename(defaultextension=".mid", filetypes=[("MIDI files", "*.mid")], initialfile="output.mid")
        if save_path:
            midi_file = gpx_to_midi(gpx_filename, min_note, max_note)
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

select_button = Button(root, text="Select GPX File", command=lambda: save_midi_file(min_note_scale.get(), max_note_scale.get()))
select_button.pack(pady=20)

status_label = Label(root, text="")
status_label.pack()

# Run the Tkinter event loop
root.mainloop()
