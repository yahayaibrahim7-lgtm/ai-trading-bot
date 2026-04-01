import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class SignalPage extends StatefulWidget {
  @override
  _SignalPageState createState() => _SignalPageState();
}

class _SignalPageState extends State<SignalPage> {

  String result = "Loading...";

  @override
  void initState() {
    super.initState();
    loadSignal();
  }

  Future<void> loadSignal() async {
    final prefs = await SharedPreferences.getInstance();
    String? token = prefs.getString("token");

    final data = await ApiService.getSignal(token!);

    setState(() {
      result = data.toString();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Live Signal")),
      body: Center(child: Text(result)),
    );
  }
}