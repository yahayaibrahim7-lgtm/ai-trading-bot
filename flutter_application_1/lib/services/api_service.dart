import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = "http://192.168.0.111:5000";

  static Future<String> login(String email, String password) async {
    final res = await http.post(
      Uri.parse("$baseUrl/auth/login"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "email": email,
        "password": password
      }),
    );

    if (res.statusCode == 200) {
      return jsonDecode(res.body)["token"];
    } else {
      throw Exception("Login failed");
    }
  }

  static Future<Map<String, dynamic>> getSignal(String token) async {
    final res = await http.get(
      Uri.parse("$baseUrl/signal"),
      headers: {"Authorization": token},
    );

    return jsonDecode(res.body);
  }
}