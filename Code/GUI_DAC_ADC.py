import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time

import IBM4_Lib


MIN_VOLTAGE = 0.0
MAX_VOLTAGE = 4.095
GAIN_MAX_VOLTAGE = {1: 2.048, 2: 4.095}
DAC_CHANNELS = ("a", "b", "c", "d")
APP_BG = "#f4f6fb"
CARD_BG = "#ffffff"
PLOT_COLORS = {"a": "#1f77b4", "b": "#d62728", "c": "#2ca02c", "d": "#9467bd"}


class DACControlGUI:
	def __init__(self):
		self.dev = IBM4_Lib.Ser_Iface()
		self.write_mcp4728 = getattr(self.dev, "MCP4728_voltage")
		self.root = tk.Tk()
		self.root.title("IBM4 DAC Slider Control")
		self.root.geometry("1120x820")
		self.root.minsize(980, 700)
		self.root.resizable(True, True)
		self.root.configure(bg=APP_BG)

		self.left_frame = tk.Frame(self.root, bg=APP_BG)
		self.left_frame.pack(side="left", fill="both", expand=True)

		self.graph_frame = tk.Frame(self.root, bg=APP_BG, width=420)
		self.graph_frame.pack(side="right", fill="y", padx=(0, 14), pady=8)
		self.graph_frame.pack_propagate(False)

		self.status_var = tk.StringVar(value="Connected")
		self.progress_var = tk.StringVar(value="Sweep Progress: Idle")
		self.value_labels = {}
		self.sliders = {}
		self.manual_entries = {}
		self.gain_vars = {}
		self.sweep_start_entries = {}
		self.sweep_end_entries = {}
		self.sweep_step_entries = {}
		self.group_channel_vars = {}
		self.channel_gains = {channel: 2 for channel in DAC_CHANNELS}
		self.last_values = {channel: None for channel in DAC_CHANNELS}
		self.sweep_thread = None
		self.stop_sweep = False
		self.ad_polling = False
		self.ad_after_id = None
		self.ad_value_var = tk.StringVar(value="AD7322 CH0: -- V")
		self._swept_channels = []
		self.device_lock = threading.RLock()
		self._ui_ready = False
		self._updating_slider = False
		self._panic_in_progress = False
		self.slider_control_var = tk.BooleanVar(value=True)
		self.plot_start_time = time.monotonic()
		self.voltage_history = {channel: [] for channel in DAC_CHANNELS}
		self.plot_canvas = None
		self.plot_legend_labels = {}

		self._build_ui()
		self._configure_dac_gain()
		self._ui_ready = True
		self.root.report_callback_exception = self._on_gui_exception
		self.root.protocol("WM_DELETE_WINDOW", self._on_close)

	def _build_ui(self):
		title = tk.Label(
			self.left_frame,
			text="Manual DAC Voltage Control",
			font=("Helvetica", 16, "bold"),
			pady=12,
			bg=APP_BG,
			fg="#182030",
		)
		title.pack()

		sliders_frame = tk.Frame(self.left_frame, padx=18, pady=8, bg=APP_BG)
		sliders_frame.pack(fill="x", expand=True)

		for index, channel in enumerate(DAC_CHANNELS):
			channel_frame = tk.Frame(sliders_frame, padx=14, pady=10, bg=CARD_BG, bd=1, relief="solid")
			channel_frame.grid(row=0, column=index, sticky="n")

			channel_label = tk.Label(
				channel_frame,
				text=f"DAC {channel.upper()}",
				font=("Helvetica", 12, "bold"),
			)
			channel_label.pack(pady=(0, 8))

			value_label = tk.Label(channel_frame, text="0.000 V", font=("Helvetica", 11))
			value_label.pack(pady=(0, 6))
			self.value_labels[channel] = value_label

			slider = tk.Scale(
				channel_frame,
				from_=self._channel_max_voltage(channel),
				to=MIN_VOLTAGE,
				orient=tk.VERTICAL,
				length=220,
				resolution=0.001,
				digits=4,
				command=lambda value, ch=channel: self._set_channel_voltage(ch, value),
			)
			slider.set(0.0)
			slider.pack()
			self.sliders[channel] = slider

			gain_frame = tk.Frame(channel_frame)
			gain_frame.pack(pady=(6, 4))
			tk.Label(gain_frame, text="Gain:").pack(side="left")
			gain_var = tk.StringVar(value="2")
			self.gain_vars[channel] = gain_var
			gain_menu = tk.OptionMenu(gain_frame, gain_var, "1", "2")
			gain_menu.config(width=3)
			gain_menu.pack(side="left", padx=3)
			tk.Button(
				gain_frame,
				text="Apply",
				command=lambda ch=channel: self._apply_channel_gain(ch),
			).pack(side="left")

			manual_frame = tk.Frame(channel_frame)
			manual_frame.pack(pady=(8, 4))
			tk.Label(manual_frame, text="Set V:").pack(side="left")
			manual_entry = tk.Entry(manual_frame, width=6)
			manual_entry.insert(0, "0.000")
			manual_entry.pack(side="left", padx=3)
			self.manual_entries[channel] = manual_entry
			tk.Button(
				manual_frame,
				text="Set",
				command=lambda ch=channel: self._set_channel_from_entry(ch),
			).pack(side="left")

			sweep_frame = tk.Frame(channel_frame)
			sweep_frame.pack(pady=(6, 0))
			tk.Label(sweep_frame, text="V1").grid(row=0, column=0)
			tk.Label(sweep_frame, text="V2").grid(row=0, column=1)
			tk.Label(sweep_frame, text="dV").grid(row=0, column=2)

			start_entry = tk.Entry(sweep_frame, width=5)
			start_entry.insert(0, "0.0")
			start_entry.grid(row=1, column=0, padx=1)
			self.sweep_start_entries[channel] = start_entry

			end_entry = tk.Entry(sweep_frame, width=5)
			end_entry.insert(0, "1.0")
			end_entry.grid(row=1, column=1, padx=1)
			self.sweep_end_entries[channel] = end_entry

			step_entry = tk.Entry(sweep_frame, width=5)
			step_entry.insert(0, "0.1")
			step_entry.grid(row=1, column=2, padx=1)
			self.sweep_step_entries[channel] = step_entry

			tk.Button(
				sweep_frame,
				text="Sweep",
				command=lambda ch=channel: self._start_single_channel_sweep(ch),
			).grid(row=2, column=0, columnspan=3, pady=(3, 0), sticky="ew")

		group_frame = tk.Frame(self.left_frame, padx=10, pady=8, bg=APP_BG)
		group_frame.pack(fill="x")
		tk.Label(group_frame, text="Group Sweep").grid(row=0, column=0, padx=(0, 6))
		tk.Label(group_frame, text="V1").grid(row=0, column=1)
		tk.Label(group_frame, text="V2").grid(row=0, column=2)
		tk.Label(group_frame, text="dV").grid(row=0, column=3)
		tk.Label(group_frame, text="Delay(s)").grid(row=0, column=4)

		self.group_start_entry = tk.Entry(group_frame, width=6)
		self.group_start_entry.insert(0, "0.0")
		self.group_start_entry.grid(row=1, column=1, padx=2)

		self.group_end_entry = tk.Entry(group_frame, width=6)
		self.group_end_entry.insert(0, "1.0")
		self.group_end_entry.grid(row=1, column=2, padx=2)

		self.group_step_entry = tk.Entry(group_frame, width=6)
		self.group_step_entry.insert(0, "0.1")
		self.group_step_entry.grid(row=1, column=3, padx=2)

		self.delay_entry = tk.Entry(group_frame, width=7)
		self.delay_entry.insert(0, "0.20")
		self.delay_entry.grid(row=1, column=4, padx=2)

		checkbox_frame = tk.Frame(group_frame)
		checkbox_frame.grid(row=1, column=5, padx=(8, 2))
		for idx, channel in enumerate(DAC_CHANNELS):
			var = tk.BooleanVar(value=True)
			self.group_channel_vars[channel] = var
			tk.Checkbutton(checkbox_frame, text=channel.upper(), variable=var).grid(row=0, column=idx)

		tk.Button(group_frame, text="Sweep Selected", command=self._start_group_sweep).grid(row=1, column=6, padx=(8, 2))
		tk.Button(group_frame, text="Stop Sweep", command=self._stop_sweep).grid(row=1, column=7, padx=2)
		tk.Button(group_frame, text="Reset/Reconnect IBM4", command=self._reset_reconnect_ibm4).grid(row=1, column=8, padx=(8, 2))
		tk.Checkbutton(group_frame, text="Enable Sliders", variable=self.slider_control_var, command=self._sync_slider_state).grid(row=2, column=6, columnspan=3, sticky="w", padx=(8, 2), pady=(6, 0))

		ad_frame = tk.Frame(self.left_frame, padx=10, pady=8, bg=APP_BG)
		ad_frame.pack(fill="x")
		tk.Label(ad_frame, text="AD7322 Measure").grid(row=0, column=0, padx=(0, 8))
		tk.Label(ad_frame, text="Channel").grid(row=0, column=1)
		self.ad_channel_var = tk.StringVar(value="0")
		tk.OptionMenu(ad_frame, self.ad_channel_var, "0", "1", "2", "3", "4", "5", "6", "7").grid(row=0, column=2, padx=3)
		tk.Label(ad_frame, text="Period (ms)").grid(row=0, column=3)
		self.ad_period_entry = tk.Entry(ad_frame, width=7)
		self.ad_period_entry.insert(0, "500")
		self.ad_period_entry.grid(row=0, column=4, padx=3)
		tk.Button(ad_frame, text="Read AD7322", command=self._read_ad7322_once).grid(row=0, column=5, padx=(8, 2))
		tk.Button(ad_frame, text="Start Auto", command=self._start_ad_poll).grid(row=0, column=6, padx=2)
		tk.Button(ad_frame, text="Stop Auto", command=self._stop_ad_poll).grid(row=0, column=7, padx=2)
		tk.Label(ad_frame, textvariable=self.ad_value_var, font=("Helvetica", 11, "bold")).grid(row=0, column=8, padx=(10, 2), sticky="w")

		zero_button = tk.Button(
			self.left_frame,
			text="Zero All Channels",
			command=self._zero_all_channels,
			font=("Helvetica", 11, "bold"),
			padx=12,
			pady=6,
		)
		zero_button.pack(pady=(4, 6))

		status_label = tk.Label(
			self.left_frame,
			textvariable=self.status_var,
			anchor="w",
			padx=10,
			pady=10,
			fg="#1f4d1f",
			bg=APP_BG,
		)
		status_label.pack(fill="x")

		progress_label = tk.Label(
			self.left_frame,
			textvariable=self.progress_var,
			anchor="w",
			padx=10,
			pady=2,
			fg="#2f2f7f",
			bg=APP_BG,
		)
		progress_label.pack(fill="x")

		plot_title = tk.Label(self.graph_frame, text="Voltage Set Over Time", bg=APP_BG, fg="#182030", font=("Helvetica", 12, "bold"))
		plot_title.pack(anchor="w", padx=8, pady=(4, 4))
		self.plot_canvas = tk.Canvas(self.graph_frame, width=390, height=320, bg="#ffffff", highlightthickness=1, highlightbackground="#cfd6e4")
		self.plot_canvas.pack(fill="x", expand=False, padx=8)

		legend_frame = tk.Frame(self.graph_frame, bg=APP_BG)
		legend_frame.pack(fill="x", padx=8, pady=(8, 0))
		for channel in DAC_CHANNELS:
			row = tk.Frame(legend_frame, bg=APP_BG)
			row.pack(anchor="w")
			chip = tk.Label(row, text="  ", bg=PLOT_COLORS[channel])
			chip.pack(side="left", padx=(0, 6), pady=1)
			label = tk.Label(row, text=f"DAC {channel.upper()}", bg=APP_BG)
			label.pack(side="left")
			self.plot_legend_labels[channel] = label

		self._redraw_plot()

	def _configure_dac_gain(self):
		for channel in DAC_CHANNELS:
			self._apply_channel_gain(channel, initial=True)
		self._sync_slider_state()

	def _sync_slider_state(self):
		state = tk.NORMAL if self.slider_control_var.get() else tk.DISABLED
		for slider in self.sliders.values():
			slider.configure(state=state)

	def _record_voltage_point(self, channel, voltage):
		elapsed = time.monotonic() - self.plot_start_time
		self.voltage_history[channel].append((elapsed, voltage))
		if len(self.voltage_history[channel]) > 2000:
			self.voltage_history[channel] = self.voltage_history[channel][-2000:]
		self._redraw_plot()

	def _redraw_plot(self):
		if self.plot_canvas is None:
			return

		canvas = self.plot_canvas
		canvas.delete("all")
		width = int(canvas.winfo_width() or 390)
		height = int(canvas.winfo_height() or 320)
		pad_left = 42
		pad_right = 12
		pad_top = 12
		pad_bottom = 30
		plot_width = max(1, width - pad_left - pad_right)
		plot_height = max(1, height - pad_top - pad_bottom)
		max_voltage = 4.096
		window = 60.0
		now = time.monotonic() - self.plot_start_time
		start_time = max(0.0, now - window)

		canvas.create_rectangle(pad_left, pad_top, pad_left + plot_width, pad_top + plot_height, outline="#d5dbe8")
		for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
			v = max_voltage * fraction
			y = pad_top + plot_height - (v / max_voltage) * plot_height
			canvas.create_line(pad_left, y, pad_left + plot_width, y, fill="#eef1f7")
			canvas.create_text(pad_left - 8, y, text=f"{v:.1f}", anchor="e", fill="#667")

		for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
			t = start_time + window * fraction
			x = pad_left + (t - start_time) / window * plot_width if window > 0 else pad_left
			canvas.create_line(x, pad_top, x, pad_top + plot_height, fill="#eef1f7")
			canvas.create_text(x, pad_top + plot_height + 10, text=f"{t:0.0f}", anchor="n", fill="#667")

		canvas.create_text(pad_left, pad_top - 2, text="V", anchor="sw", fill="#667")
		canvas.create_text(pad_left + plot_width, pad_top + plot_height + 10, text="s", anchor="n", fill="#667")

		for channel in DAC_CHANNELS:
			points = [(t, v) for t, v in self.voltage_history[channel] if t >= start_time]
			if len(points) < 2:
				continue
			coords = []
			for t, v in points:
				x = pad_left + ((t - start_time) / window) * plot_width if window > 0 else pad_left
				y = pad_top + plot_height - (max(0.0, min(v, max_voltage)) / max_voltage) * plot_height
				coords.extend([x, y])
			canvas.create_line(*coords, fill=PLOT_COLORS[channel], width=2)

	def _on_gui_exception(self, exc_type, exc_value, exc_traceback):
		if self._panic_in_progress:
			return
		self._panic_in_progress = True
		try:
			message = str(exc_value)
			self.status_var.set(f"GUI error: {message}")
			self.stop_sweep = True
			self._stop_ad_poll()
			self._safe_zero_all_channels()
			if self._is_timeout_error(exc_value):
				self._reset_reconnect_ibm4()
		finally:
			self._panic_in_progress = False

	def _safe_zero_all_channels(self):
		try:
			self._zero_all_channels()
		except Exception:
			pass

	def _set_status(self, message):
		if threading.current_thread() is threading.main_thread():
			self.status_var.set(message)
		else:
			self.root.after(0, lambda msg=message: self.status_var.set(msg))

	def _set_progress(self, message):
		if threading.current_thread() is threading.main_thread():
			self.progress_var.set(message)
		else:
			self.root.after(0, lambda msg=message: self.progress_var.set(msg))

	def _is_sweep_running(self):
		return self.sweep_thread is not None and self.sweep_thread.is_alive()

	def _set_channel_voltage(self, channel, value):
		try:
			if not self._ui_ready:
				return
			if not self.slider_control_var.get() and not self._updating_slider:
				return
			if self._is_sweep_running() and not self._updating_slider:
				self._set_status("Stop the active sweep before changing DAC channels manually")
				return

			if not self._is_comms_open():
				self._set_status("IBM4 serial link is not open")
				return

			voltage = float(value)
			max_voltage = self._channel_max_voltage(channel)
			if voltage < MIN_VOLTAGE or voltage > max_voltage:
				raise ValueError(f"voltage must be between {MIN_VOLTAGE:.3f} and {max_voltage:.3f} V for gain {self.channel_gains[channel]}")

			if self.last_values[channel] is not None and abs(self.last_values[channel] - voltage) < 1e-6:
				return

			# Route every GUI write through IBM4_Lib.Ser_Iface.MCP4728_voltage.
			if not self._write_voltage_or_reconnect(channel, voltage):
				return
			self.last_values[channel] = voltage
			self.value_labels[channel].config(text=f"{voltage:.3f} V")
			self.status_var.set(f"MCP4728_voltage -> DAC {channel.upper()} = {voltage:.3f} V")
		except Exception as exc:
			self.status_var.set(f"Error setting DAC {channel.upper()}: {exc}")

	def _set_channel_from_entry(self, channel):
		try:
			if self._is_sweep_running():
				self._set_status("Stop the active sweep before changing DAC channels manually")
				return
			voltage = self._validate_voltage(self.manual_entries[channel].get(), channel)
			self._apply_voltage(channel, voltage, update_slider=True)
		except Exception as exc:
			self._set_status(f"Invalid value for DAC {channel.upper()}: {exc}")

	def _start_single_channel_sweep(self, channel):
		try:
			v1 = self._validate_voltage(self.sweep_start_entries[channel].get(), channel)
			v2 = self._validate_voltage(self.sweep_end_entries[channel].get(), channel)
			step = self._validate_positive_float(self.sweep_step_entries[channel].get(), "step")
			delay = self._validate_positive_float(self.delay_entry.get(), "delay")
			values = self._build_sweep_values(v1, v2, step)
			self._launch_sweep_thread([channel], values, delay)
		except Exception as exc:
			self.status_var.set(f"Sweep setup error (DAC {channel.upper()}): {exc}")

	def _start_group_sweep(self):
		try:
			channels = [ch for ch in DAC_CHANNELS if self.group_channel_vars[ch].get()]
			if not channels:
				raise ValueError("select at least one channel")

			group_max = min(self._channel_max_voltage(ch) for ch in channels)
			v1 = self._validate_voltage(self.group_start_entry.get(), max_voltage=group_max)
			v2 = self._validate_voltage(self.group_end_entry.get(), max_voltage=group_max)
			step = self._validate_positive_float(self.group_step_entry.get(), "step")
			delay = self._validate_positive_float(self.delay_entry.get(), "delay")
			values = self._build_sweep_values(v1, v2, step)
			self._launch_sweep_thread(channels, values, delay)
		except Exception as exc:
			self.status_var.set(f"Group sweep setup error: {exc}")

	def _launch_sweep_thread(self, channels, values, delay):
		if self.sweep_thread is not None and self.sweep_thread.is_alive():
			self.status_var.set("A sweep is already running")
			return

		if not self._is_comms_open():
			self.status_var.set("IBM4 serial link is not open")
			return

		self.stop_sweep = False
		self.sweep_thread = threading.Thread(
			target=self._run_sweep_worker,
			args=(channels, values, delay),
			daemon=True,
		)
		self._swept_channels = list(channels)
		self.sweep_thread.start()
		channel_list = ",".join(ch.upper() for ch in channels)
		self.progress_var.set(f"Sweep Progress: 0/{len(values)} on {channel_list}")
		self.status_var.set(f"Sweep started on {channel_list}")

	def _run_sweep_worker(self, channels, values, delay):
		total = len(values)
		channel_list = ",".join(ch.upper() for ch in channels)
		for idx, voltage in enumerate(values, start=1):
			if self.stop_sweep:
				self.root.after(0, lambda: self.status_var.set("Sweep stopped"))
				self.root.after(0, lambda: self.progress_var.set("Sweep Progress: Stopped"))
				self.root.after(0, self._zero_all_channels)
				return

			for channel in channels:
				if self.stop_sweep:
					self.root.after(0, lambda: self.status_var.set("Sweep stopped"))
					self.root.after(0, lambda: self.progress_var.set("Sweep Progress: Stopped"))
					self.root.after(0, self._zero_all_channels)
					return

				if not self._write_voltage_or_reconnect(channel, voltage):
					return
				self.root.after(0, lambda ch=channel, v=voltage: self._update_channel_ui(ch, v))

			self.root.after(
				0,
				lambda i=idx, t=total, v=voltage, cl=channel_list: self.progress_var.set(
					f"Sweep Progress: {i}/{t} | V={v:.3f} V | Channels={cl}"
				),
			)

			time.sleep(delay)

		self.root.after(0, self._finish_sweep)

	def _stop_sweep(self):
		self.stop_sweep = True

	def _is_timeout_error(self, exc):
		message = str(exc).lower()
		return "timeout" in message or "timed out" in message

	def _handle_timeout_and_reconnect(self, exc, context):
		if self._is_timeout_error(exc):
			self.stop_sweep = True
			self.ad_polling = False
			self._set_status(f"{context} timed out, reconnecting IBM4...")
			self._set_progress("Sweep Progress: Idle")
			self.root.after(0, self._reset_reconnect_ibm4)
			return True
		return False

	def _write_voltage_or_reconnect(self, channel, voltage):
		try:
			with self.device_lock:
				self.write_mcp4728(val=voltage, output=channel)
			return True
		except Exception as exc:
			if self._handle_timeout_and_reconnect(exc, f"DAC {channel.upper()} write"):
				return False
			self._set_status(f"Error setting DAC {channel.upper()}: {exc}")
			return False

	def _apply_gain_or_reconnect(self, channel, gain):
		try:
			with self.device_lock:
				self.dev.gain_settings(channel=channel, gain=gain)
			return True
		except Exception as exc:
			if self._handle_timeout_and_reconnect(exc, f"DAC {channel.upper()} gain write"):
				return False
			self._set_status(f"Gain update failed for DAC {channel.upper()}: {exc}")
			return False

	def _apply_channel_gain(self, channel, initial=False):
		try:
			if not self._is_comms_open():
				self.status_var.set("IBM4 serial link is not open")
				return

			gain = int(self.gain_vars[channel].get()) if not initial else 2
			if gain not in (1, 2):
				raise ValueError("gain must be 1 or 2")

			if not self._apply_gain_or_reconnect(channel, gain):
				return
			self.channel_gains[channel] = gain
			self.sliders[channel].configure(from_=self._channel_max_voltage(channel), to=MIN_VOLTAGE)

			current_value = self.last_values.get(channel)
			if current_value is not None and current_value > self._channel_max_voltage(channel):
				current_value = self._channel_max_voltage(channel)
				if not self._write_voltage_or_reconnect(channel, current_value):
					return
				self._update_channel_ui(channel, current_value, update_slider=True)

			self.status_var.set(f"DAC {channel.upper()} gain set to {gain}x")
		except Exception as exc:
			self.status_var.set(f"Gain update failed for DAC {channel.upper()}: {exc}")

	def _finish_sweep(self):
		self._zero_all_channels()
		self.status_var.set("Sweep complete")
		self.progress_var.set("Sweep Progress: Complete")
		self.sweep_thread = None

	def _zero_swept_channels(self):
		try:
			if not self._is_comms_open():
				return

			for channel in self._swept_channels:
				if not self._write_voltage_or_reconnect(channel, 0.0):
					return
				self._update_channel_ui(channel, 0.0, update_slider=True)
		except Exception as exc:
			self.status_var.set(f"Post-sweep zero failed: {exc}")
		finally:
			self._swept_channels = []

	def _read_ad7322_once(self):
		try:
			if self.sweep_thread is not None and self.sweep_thread.is_alive():
				self.status_var.set("Stop sweep before AD7322 read")
				return

			if not self._is_comms_open():
				self.status_var.set("IBM4 serial link is not open")
				return

			channel = int(self.ad_channel_var.get())
			with self.device_lock:
				voltage = self.dev.AD7322_voltage(channel)
			if voltage is None:
				self.status_var.set("AD7322 read failed")
				return

			self.ad_value_var.set(f"AD7322 CH{channel}: {voltage:.4f} V")
			self.status_var.set(f"AD7322 measurement updated (CH{channel})")
		except Exception as exc:
			if self._handle_timeout_and_reconnect(exc, "AD7322 read"):
				return
			self.status_var.set(f"AD7322 read error: {exc}")

	def _start_ad_poll(self):
		try:
			period_ms = int(float(self.ad_period_entry.get()))
			if period_ms < 50:
				period_ms = 50
			self.ad_polling = True
			self._schedule_ad_poll(period_ms)
			self.status_var.set("AD7322 auto-read started")
		except Exception as exc:
			self.status_var.set(f"AD7322 auto-read setup error: {exc}")

	def _schedule_ad_poll(self, period_ms):
		if not self.ad_polling:
			return

		self._read_ad7322_once()
		self.ad_after_id = self.root.after(period_ms, lambda: self._schedule_ad_poll(period_ms))

	def _stop_ad_poll(self):
		self.ad_polling = False
		if self.ad_after_id is not None:
			try:
				self.root.after_cancel(self.ad_after_id)
			except Exception:
				pass
			self.ad_after_id = None
		self.status_var.set("AD7322 auto-read stopped")

	def _reset_reconnect_ibm4(self):
		try:
			self.stop_sweep = True
			if self.sweep_thread is not None and self.sweep_thread.is_alive():
				self.sweep_thread.join(timeout=1.5)

			self.status_var.set("Resetting IBM4 connection...")
			self.progress_var.set("Sweep Progress: Idle")

			old_dev = self.dev
			try:
				if old_dev is not None and old_dev.instr_obj is not None and old_dev.instr_obj.isOpen():
					old_dev.instr_obj.close()
			except Exception:
				pass

			time.sleep(0.25)

			self.dev = IBM4_Lib.Ser_Iface()
			self.write_mcp4728 = getattr(self.dev, "MCP4728_voltage")
			self._configure_dac_gain()

			for channel in DAC_CHANNELS:
				if not self._write_voltage_or_reconnect(channel, 0.0):
					return
				self._update_channel_ui(channel, 0.0, update_slider=True)

			self.status_var.set("IBM4 disconnected and reconnected successfully")
		except Exception as exc:
			self.status_var.set(f"Reconnect failed: {exc}")

	def _build_sweep_values(self, v1, v2, step):
		delta = abs(step)
		if abs(v2 - v1) < 1e-12:
			return [v1]

		direction = 1 if v2 > v1 else -1
		values = []
		v = v1
		while (v <= v2 + 1e-9) if direction > 0 else (v >= v2 - 1e-9):
			values.append(round(v, 6))
			v += direction * delta

		if abs(values[-1] - v2) > 1e-6:
			values.append(v2)
		return values

	def _validate_voltage(self, value, channel=None, max_voltage=None):
		voltage = float(value)
		if max_voltage is None and channel is not None:
			max_voltage = self._channel_max_voltage(channel)
		if max_voltage is None:
			max_voltage = MAX_VOLTAGE
		if voltage < MIN_VOLTAGE or voltage > max_voltage:
			raise ValueError(f"voltage must be between {MIN_VOLTAGE:.3f} and {max_voltage:.3f}")
		return voltage

	def _channel_max_voltage(self, channel):
		gain = int(self.channel_gains.get(channel, 2))
		return GAIN_MAX_VOLTAGE.get(gain, MAX_VOLTAGE)

	def _validate_positive_float(self, value, name):
		parsed = float(value)
		if parsed <= 0:
			raise ValueError(f"{name} must be > 0")
		return parsed

	def _is_comms_open(self):
		try:
			return self.dev.instr_obj is not None and self.dev.instr_obj.isOpen()
		except Exception:
			return False

	def _apply_voltage(self, channel, voltage, update_slider=False):
		if self._is_sweep_running() and not update_slider:
			self._set_status("Stop the active sweep before changing DAC channels manually")
			return

		if not self._is_comms_open():
			self._set_status("IBM4 serial link is not open")
			return

		if not self._write_voltage_or_reconnect(channel, voltage):
			return
		self._update_channel_ui(channel, voltage, update_slider)

	def _update_channel_ui(self, channel, voltage, update_slider=False):
		self.last_values[channel] = voltage
		self.value_labels[channel].config(text=f"{voltage:.3f} V")
		self.manual_entries[channel].delete(0, tk.END)
		self.manual_entries[channel].insert(0, f"{voltage:.3f}")
		if update_slider:
			self._updating_slider = True
			try:
				self.sliders[channel].set(voltage)
			finally:
				self._updating_slider = False
		self._record_voltage_point(channel, voltage)
		self.status_var.set(f"MCP4728_voltage -> DAC {channel.upper()} = {voltage:.3f} V")

	def _zero_all_channels(self):
		try:
			if not self._is_comms_open():
				self.status_var.set("IBM4 serial link is not open")
				return

			for channel in DAC_CHANNELS:
				if not self._write_voltage_or_reconnect(channel, 0.0):
					return
				self.last_values[channel] = 0.0
				self.value_labels[channel].config(text="0.000 V")
				self._updating_slider = True
				try:
					self.sliders[channel].set(0.0)
				finally:
					self._updating_slider = False
				self._record_voltage_point(channel, 0.0)

			self.status_var.set("MCP4728_voltage -> all DAC channels set to 0.000 V")
		except Exception as exc:
			self.status_var.set(f"Error zeroing channels: {exc}")

	def _on_close(self):
		self.stop_sweep = True
		self._stop_ad_poll()
		try:
			self._zero_all_channels()
		except Exception:
			pass

		try:
			del self.dev
		except Exception:
			pass

		self.root.destroy()

	def run(self):
		try:
			self.root.mainloop()
		except Exception as exc:
			messagebox.showerror("GUI Error", str(exc))


if __name__ == "__main__":
	app = DACControlGUI()
	app.run()
