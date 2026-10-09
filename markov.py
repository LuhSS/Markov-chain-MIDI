import random
import mido
import argparse

from collections import defaultdict


def extract_notes_from_midi(files, quantize=120):
    """
    Extracts a sequence of (note, duration) tuples from the MIDI files.
    Simplifies treating it as a sequential stream of notes.
    """
    sequence = []
    resolution = 480 # Default fallback

    for file in files:
        try:
            mid = mido.MidiFile(file)
            if hasattr(mid, 'ticks_per_beat'):
                resolution = mid.ticks_per_beat
                
            for track in mid.tracks:
                current_tick = 0
                active_note = None
                
                for msg in track:
                    current_tick += msg.time
                    
                    if msg.type == 'note_on' and msg.velocity != 0:
                        if active_note is not None:
                            # Save previous note and rounded time elapsed
                            rounded_time = int(round(current_tick / quantize) * quantize)
                            
                            # Prevent notes from being rounded to 0
                            if rounded_time == 0 and current_tick > 0:
                                rounded_time = quantize
                            sequence.append((active_note, rounded_time))

                        active_note = msg.note
                        current_tick = 0
                        
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        if active_note == msg.note:
                            rounded_time = int(round(current_tick / quantize) * quantize)
                            if rounded_time == 0 and current_tick > 0:
                                rounded_time = quantize

                            sequence.append((active_note, rounded_time))
                            active_note = None
                            current_tick = 0
        except Exception as e:
            print(f"Error reading {file}: {e}")

    return sequence, resolution

def build_markov_chain(sequence, order):
    """
    Builds a dictionary mapping a tuple of 'order' notes to a list of possible next notes.
    """
    chain = defaultdict(list)
    for i in range(len(sequence) - order):
        state = tuple(sequence[i:i + order])
        next_state = sequence[i + order]
        chain[state].append(next_state)
    #print(chain)
    return chain

def generate_sequence(chain, order, max_notes, max_repeat=3, max_oscillation=6):
    """
    Generates a new sequence of notes by walking the Markov chain.
    """
    if not chain:
        return []
    
    # Pick a random starting state
    current_state = random.choice(list(chain.keys()))
    generated = list(current_state)

    for _ in range(max_notes - order):
        choices = chain[current_state]

        if choices:
            options = choices
            
            # 1. Prevent single note repeating
            recent_single = [n[0] for n in generated[-max_repeat:]]
            if len(recent_single) == max_repeat and len(set(recent_single)) == 1:
                repeating = recent_single[0]
                filtered = [c for c in options if c[0] != repeating]
                options = filtered if filtered else options

            # 2. Prevent 2-note oscillation (e.g., A-B-A-B-A-B)
            recent_oscillation = [n[0] for n in generated[-max_oscillation:]]
            if len(recent_oscillation) == max_oscillation and len(set(recent_oscillation)) <= 2:
                banned_notes = set(recent_oscillation)
                filtered = [c for c in options if c[0] not in banned_notes]
                # Fallback to the available options if filtering removes everything
                options = filtered if filtered else options          

            next_note = random.choice(options)
            generated.append(next_note)
            current_state = tuple(generated[-order:])
        else:
            # Dead end, pick new random starting point
            current_state = random.choice(list(chain.keys()))

    return generated

def write_midi_file(sequence, output_file, resolution):
    """
    Converts the generated sequence of (note, duration) back into a MIDI file.
    """
    mid = mido.MidiFile(ticks_per_beat=resolution)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    # Set a default tempo (120 BPM)
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(125)))
    
    for note, duration in sequence:
        track.append(mido.Message('note_on', note=note, velocity=80, time=0))
        track.append(mido.Message('note_off', note=note, velocity=64, time=duration))
        
    mid.save(output_file)
    print(f"Generated music saved to {output_file}")


import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter

def visualize_chain(chain, max_transitions=50):
    """
    Draws a visual graph of the Markov chain.
    Limits to 'max_transitions' to keep the graph readable.
    """
    G = nx.DiGraph()
    all_edges = []

    # 1. Count the frequencies of each transition
    for state, next_notes in chain.items():
        # Count how many times each next note appears for this state
        counts = Counter(next_notes)
        
        for next_note, count in counts.items():
            # To make labels readable, extract just the note pitches (ignoring durations)
            state_pitches = str([note[0] for note in state])
            
            # The next state drops the oldest note and adds the new one
            next_state = state[1:] + (next_note,)
            next_state_pitches = str([note[0] for note in next_state])
            
            all_edges.append((state_pitches, next_state_pitches, count))

    # 2. Sort by frequency and take only the top X transitions to avoid clutter
    all_edges.sort(key=lambda x: x[2], reverse=True)
    top_edges = all_edges[:max_transitions]

    # 3. Add the edges to the NetworkX graph
    for u, v, weight in top_edges:
        G.add_edge(u, v, weight=weight)

    # 4. Draw the graph
    plt.figure(figsize=(12, 8))
    
    # Calculate layout positions for nodes to space them out
    pos = nx.spring_layout(G, k=0.9, iterations=50)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=2000, node_color='lightblue', alpha=0.8)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    
    # Draw edges, adjusting thickness based on how frequently the transition happens
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    # Normalize line thickness for the visual
    max_weight = max(edge_weights) if edge_weights else 1
    normalized_widths = [(w / max_weight) * 4 for w in edge_weights]
    
    nx.draw_networkx_edges(G, pos, width=normalized_widths, arrows=True, arrowsize=20, edge_color='gray', alpha=0.6)

    plt.title(f"Markov Chain Note Transitions (Top {max_transitions} most frequent)")
    plt.axis('off')
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate music using Markov chains.")
    parser.add_argument("files", metavar="MIDI_FILE", type=str, nargs="+", help="One or more MIDI files to use as input")
    parser.add_argument("-o", "--order", type=int, default=3, help="Order of the Markov chain (default: 3)")
    parser.add_argument("-of", "--output-file", type=str, default="output.mid", help="Output MIDI file name (default: output.mid)")
    parser.add_argument("-n", "--max-notes", type=int, default=150, help="Maximum number of notes to generate (default: 150)")
    parser.add_argument("-s", "--seed", type=int, default=None, help="Seed")
    parser.add_argument("-v", "--visualize", action="store_true", help="Show a visual graph of the generated Markov chain")
    
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    print(f"Extracting notes from {len(args.files)} file(s)...")
    source_sequence, resolution = extract_notes_from_midi(args.files)

    print(f"Building Markov chain (Order: {args.order})...")
    markov_chain = build_markov_chain(source_sequence, args.order)

    print(f"Generating new sequence of {args.max_notes} notes...")
    generated_sequence = generate_sequence(markov_chain, args.order, args.max_notes)

    write_midi_file(generated_sequence, args.output_file, resolution)

    if args.visualize:
        print("Opening visualization window...")
        visualize_chain(markov_chain)