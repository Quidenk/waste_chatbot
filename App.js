import { useState } from 'react';
import { 
  StyleSheet, Text, View, ScrollView, TextInput, TouchableOpacity, 
  KeyboardAvoidingView, Platform, Image
} from 'react-native';
import AntIcon from "react-native-vector-icons/AntDesign";
import Icon from 'react-native-vector-icons/FontAwesome';
import { SafeAreaView } from "react-native-safe-area-context";
import * as ImagePicker from 'expo-image-picker';
import axios from 'axios';

const SERVER_URL = "http://192.168.100.200:5000";

export default function App() {
  const [messages, setMessages] = useState([
    { text: "Xin chào! Tôi là chatbot xử lý rác thải. Bạn cần giúp gì?", sender: "bot" }
  ]);
  const [inputText, setInputText] = useState("");

  // const handleSendMessage = async () => {
  //   if (!inputText.trim()) return;
    
  //   const newMessages = [...messages, { text: inputText, sender: "user" }];
  //   setMessages(newMessages);
  //   setInputText("");

  //   try {
  //     const response = await axios.post(`${SERVER_URL}/chat`, { message: inputText });
  //     console.log(">>>>>response :", response)
  //     setMessages([...newMessages, { text: response.data.reply, sender: "bot" }]);
  //   } catch (error) {
  //     setMessages([...newMessages, { text: "Lỗi khi gửi tin nhắn!", sender: "bot" }]);
  //   }
  // };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;
  
    const newMessages = [...messages, { text: inputText, sender: "user" }];
    setMessages(newMessages);
    setInputText("");
  
    try {
      const response = await axios.post(`${SERVER_URL}/chat`, { message: inputText });
      console.log(">>>>>response :", response);
      setMessages([...newMessages, { text: response.data.response, sender: "bot" }]);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages([...newMessages, { text: "Lỗi khi gửi tin nhắn!", sender: "bot" }]);
    }
  };
  

  const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 1,
    });

    if (!result.canceled) {
      const newMessages = [...messages, { image: result.assets[0].uri, sender: "user" }];
      setMessages(newMessages);
      handleSendImage(result.assets[0].uri, newMessages);
    }
  };

  const handleSendImage = async (imageUri, currentMessages) => {
    const formData = new FormData();
    formData.append("image", {
      uri: imageUri,
      type: "image/jpeg",
      name: "image.jpg",
    });

    setMessages([...currentMessages, { text: "Đang phân tích ảnh...", sender: "bot" }]);

    try {
      const response = await axios.post(`${SERVER_URL}/predict`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log(">>>>>>response: ", response.data);

      const predictions = response.data.predictions;

      let newMessages = [...currentMessages, { text: "Ảnh đã được phân tích!", sender: "bot" }];

      for (const item of predictions) {
        newMessages.push({
          text: `Phát hiện: ${item.label} (${item.confidence}%)`,
          sender: "bot"
        });

        if (item.image) {
          newMessages.push({ image: item.image, sender: "bot" });
        }

        const solutionRes = await axios.post(`${SERVER_URL}/get_solution`, { type: item.label });

        newMessages.push({ text: `🗑 Giải pháp: \n\ ${solutionRes.data.solution}`, sender: "bot" });
      }

      setMessages(newMessages);
    } catch (error) {
      console.error("Lỗi khi xử lý ảnh:", error);
      setMessages([...currentMessages, { text: "Lỗi khi nhận diện ảnh!!!", sender: "bot" }]);
    }
  };


  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView style={styles.chatbot} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <View style={styles.textArea}>
          <Text style={styles.NameChatbot}>Waste Treatment Chatbot</Text>

          <ScrollView style={styles.Area} contentContainerStyle={{ paddingBottom: 20 }}>
            {messages.map((msg, index) => (
              <View key={index} style={msg.sender === "user" ? styles.userMessage : styles.botMessage}>
                {msg.text && <Text style={styles.messageText}>{msg.text}</Text>}
                {msg.image && <Image source={{ uri: msg.image }} style={styles.imagePreview} />}
              </View>
            ))}
          </ScrollView>
        </View>

        <View style={styles.inputContainer}>
          <TouchableOpacity style={styles.uploadButton} onPress={pickImage}>
            <Text style={styles.uploadText}><AntIcon name="picture" size={24} color="#0078FF" /></Text>
          </TouchableOpacity>
          <TextInput style={styles.input} value={inputText} onChangeText={setInputText} placeholder="Nhập tin nhắn..." placeholderTextColor="#aaa" />
          <TouchableOpacity style={styles.sendButton} onPress={handleSendMessage}>
            <Text style={styles.sendText}><Icon name="paper-plane" size={24} color="#0078FF" /></Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#101010"},
  chatbot: { flex: 1 },
  NameChatbot: { color: "#fff", fontSize: 22, fontWeight: "bold", textAlign: "center", paddingVertical: 15, backgroundColor: "tranparent" , paddingTop: Platform.OS === "ios" ? 50 : 15},
  textArea: { flex: 1, paddingHorizontal: 18 },
  Area: { flexGrow: 1, marginTop: 10 },
  userMessage: { alignSelf: "flex-end", backgroundColor: "#0078FF", padding: 12, borderRadius: 10, marginVertical: 5, maxWidth: "75%" },
  botMessage: { alignSelf: "flex-start", backgroundColor: "#444", padding: 12, borderRadius: 10, marginVertical: 5, maxWidth: "75%" },
  messageText: { color: "#fff", fontSize: 16 },
  inputContainer: { flexDirection: "row", alignItems: "center", padding: 12, backgroundColor: "tranparent", display: "flex", justifyContent: "space-evenly" , paddingBottom: Platform.OS === "ios" ? 30 : 15},
  input: { marginLeft: 10, flex: 1, color: "#fff", backgroundColor: "#333", paddingVertical: 10, paddingHorizontal: 15, borderRadius: 5, fontSize: 16 },
  sendButton: { backgroundColor: "tranparent", paddingVertical: 10, paddingHorizontal: 18, borderRadius: 5 },
  sendText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
  uploadButton: { backgroundColor: "tranparent", paddingVertical: 10, paddingHorizontal: 15, borderRadius: 30, borderWidth: 1, borderColor: "#0078FF" },
  uploadText: { color: "#fff", fontWeight: "bold", fontSize: 16 },
  imagePreview: { width: 200, height: 200, alignSelf: "center", marginVertical: 10, borderRadius: 10 },
});
