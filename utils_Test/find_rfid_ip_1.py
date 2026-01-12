#!/usr/bin/env python3
"""
Script to run arp-scan for 30 seconds and display the output.
This simulates user running the command and stopping it with Ctrl+C after 30 seconds.
"""

import subprocess
import signal
import sys
import time
import threading
import pty
import os
import select


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n--- Scan stopped by user (Ctrl+C) ---")
    sys.exit(0)


def main():
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60)
    print("Starting ARP Scan on 169.254.0.0/16 network")
    print("=" * 60)
    print("\nRunning command: sudo arp-scan --interface=eth0 169.254.0.0/16")
    print("-" * 60)
    
    # Start the subprocess with pseudo-TTY for unbuffered output
    # This makes the subprocess think it's writing to a terminal
    master_fd, slave_fd = pty.openpty()
    
    process = subprocess.Popen(
        ["sudo", "arp-scan", "--interface=eth0", "169.254.0.0/16"],
        stdout=slave_fd,
        stderr=slave_fd,
        universal_newlines=True
    )
    os.close(slave_fd)
    
    start_time = time.time()
    timeout = 180  # 180 seconds
    
    # Use a flag to stop reading output
    should_stop = threading.Event()
    
    # Buffer to store all output
    output_buffer = []
    
    def read_output():
        """Read output from process in a separate thread"""
        try:
            while not should_stop.is_set():
                try:
                    # Use select to check if data is available for reading
                    ready, _, _ = select.select([master_fd], [], [], 0.1)
                    if ready:
                        # Read from master fd
                        data = os.read(master_fd, 1024).decode('utf-8', errors='replace')
                        if data:
                            output_buffer.append(data)
                            sys.stdout.write(data)
                            sys.stdout.flush()
                    # Check if process has ended and no more data
                    if process.poll() is not None:
                        # Try to read any remaining data
                        while True:
                            ready, _, _ = select.select([master_fd], [], [], 0.1)
                            if not ready:
                                break
                            data = os.read(master_fd, 1024).decode('utf-8', errors='replace')
                            if data:
                                output_buffer.append(data)
                                sys.stdout.write(data)
                                sys.stdout.flush()
                        break
                except OSError:
                    break
        except Exception as e:
            pass
        finally:
            os.close(master_fd)
    
    # Start output reading thread
    output_thread = threading.Thread(target=read_output, daemon=True)
    output_thread.start()
    
    try:
        # Wait for timeout or process completion
        while True:
            # Check if timeout reached
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                print("\n--- 180 seconds elapsed, stopping scan ---", flush=True)
                should_stop.set()
                process.terminate()
                # Wait a bit for graceful termination
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                break
            
            # Check if process has finished
            if process.poll() is not None:
                # Process completed
                should_stop.set()
                break
            
            time.sleep(0.05)  # Small delay to prevent CPU spinning
        
        # Wait for output thread to finish reading
        output_thread.join(timeout=2)
        
        print("\n" + "-" * 60)
        print("Scan completed.")
        print("=" * 60)
        
        # Write output to file
        try:
            with open('output.txt', 'w') as f:
                f.write(''.join(output_buffer))
            print("\nOutput saved to output.txt")
        except Exception as e:
            print(f"\nError saving output to file: {e}")
        
    except KeyboardInterrupt:
        # Handle Ctrl+C during execution
        print("\n\n--- Scan stopped by user (Ctrl+C) ---")
        should_stop.set()
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        # Save output before exiting
        try:
            with open('output.txt', 'w') as f:
                f.write(''.join(output_buffer))
        except Exception:
            pass
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        should_stop.set()
        process.terminate()
        # Save output before exiting
        try:
            with open('output.txt', 'w') as f:
                f.write(''.join(output_buffer))
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()