// Custom styles for PhoneInput country select
const phoneInputCustomStyles = `
	.PhoneInputCountrySelect {
		background-color: #230735 !important;
		color: #fff !important;
	}
	.PhoneInputCountrySelect option {
		background-color: #230735 !important;
		color: #fff !important;
	}
`;
import React, { useState } from "react";
import PhoneInput from "react-phone-number-input";
import "react-phone-number-input/style.css";
import { FiUser, FiCheck } from "react-icons/fi";
import { requestOtp, verifyOtp } from "../api";

const Login: React.FC = () => {
	const [mobile, setMobile] = useState("");
	const [otpSent, setOtpSent] = useState(false);
	const [otp, setOtp] = useState("");
	const [message, setMessage] = useState("");
	const [isLoading, setIsLoading] = useState(false);

		const handleSendOtp = async () => {
			setMessage("");
			if (!mobile) {
				setMessage("Please enter your mobile number.");
				return;
			}
			setIsLoading(true);
			try {
				const res = await requestOtp(mobile);
				setOtpSent(true);
				setMessage(res.message + (res.otp_for_testing_only ? ` (OTP: ${res.otp_for_testing_only})` : ""));
			} catch (err: any) {
				setMessage(err.message);
			}
			setIsLoading(false);
		};

		const handleSubmit = async () => {
			setMessage("");
			if (!otp) {
				setMessage("Please enter the OTP.");
				return;
			}
			setIsLoading(true);
			try {
				const res = await verifyOtp(mobile, otp);
				setMessage(res.message);
			} catch (err: any) {
				setMessage(err.message);
			}
			setIsLoading(false);
		};

		const handleResendOtp = () => {
			setOtp("");
			setMessage("");
			setOtpSent(false);
		};

	return (
				<div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#230735] to-[#11001C] p-4">
					{/* Inject custom styles for PhoneInput dropdown */}
					<style>{phoneInputCustomStyles}</style>
					<div className="w-full max-w-md bg-gradient-to-br from-[#230735] to-[#11001C] border border-purple-900/40 shadow-2xl rounded-2xl p-8 backdrop-blur-xl">
						<div className="flex flex-col items-center mb-6">
							<div className="bg-yellow-400/90 rounded-full p-3 shadow-lg mb-2">
								<FiUser className="text-[#230735] text-3xl" />
							</div>
							<h2 className="text-3xl font-extrabold text-center text-white tracking-wide">Login</h2>
							<div className="w-16 h-1 bg-gradient-to-r from-yellow-400 to-purple-700 rounded-full mt-2" />
						</div>
						<div className="space-y-6">
							<div>
								<label className="block text-white text-sm font-semibold mb-2">Mobile Number</label>
								<PhoneInput
									international
									defaultCountry="IN"
									value={mobile}
									onChange={value => setMobile(value || "")}
									className="w-full px-4 py-3 rounded-lg bg-black/40 backdrop-blur-sm text-white text-base border border-yellow-400/40 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent placeholder-gray-400 transition-all duration-300 hover:border-yellow-400/70"
								/>
							</div>
							{!otpSent && (
								<button
									type="button"
									onClick={handleSendOtp}
									className="w-full py-3 bg-gradient-to-r from-yellow-400 to-yellow-600 text-[#230735] font-bold rounded-lg shadow-lg hover:scale-105 transition-all duration-200 cursor-pointer"
								>
									Send OTP
								</button>
							)}
							{otpSent && (
								<>
									<div>
										<label className="block text-white text-sm font-semibold mb-2">Enter OTP</label>
										<input
											type="text"
											value={otp}
											onChange={e => setOtp(e.target.value)}
											placeholder="Enter OTP"
											className="w-full px-4 py-3 rounded-lg bg-black/40 backdrop-blur-sm text-white text-base border border-yellow-400/40 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent placeholder-gray-400 transition-all duration-300 hover:border-yellow-400/70"
										/>
									</div>
													<button
														type="button"
														onClick={handleSubmit}
														className="w-full py-3 mt-4 bg-gradient-to-r from-green-400 to-green-600 text-[#230735] font-bold rounded-lg shadow-lg hover:scale-105 transition-all duration-200 cursor-pointer flex items-center justify-center space-x-2"
														disabled={isLoading}
													>
														<span>Verify & Login</span>
														<FiCheck className="w-5 h-5 ml-2 text-[#230735]" />
													</button>
													<button
														type="button"
														onClick={handleResendOtp}
														className="w-full text-purple-300 text-sm hover:text-yellow-400 transition-colors duration-200 underline decoration-dotted underline-offset-4 mt-2"
														disabled={isLoading}
													>
														Didn't receive OTP? <span className="font-semibold">Resend</span>
													</button>
								</>
							)}
										{message && (
											<div className="mt-6 text-center text-yellow-300 font-semibold text-base drop-shadow-lg">{message}</div>
										)}
								</div>
								{/* Terms and Privacy */}
								<div className="mt-8 text-center">
									<p className="text-gray-300 text-xs">
										By continuing, you agree to our{' '}
										<a href="#" className="text-yellow-400 hover:text-yellow-300 underline transition-colors">Terms of Service</a>
										{' '}and{' '}
										<a href="#" className="text-yellow-400 hover:text-yellow-300 underline transition-colors">Privacy Policy</a>
									</p>
								</div>
							</div>
						</div>
	);
};

export default Login;
