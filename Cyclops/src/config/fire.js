import firebase from "firebase"

var firebaseConfig = {
    // apiKey: "4nQOP3M",
    // authDomain: "shom",
    // databaseURL: "https://shop-rebaom",
    // projectId: "shop",
    // storageBucket: "shop-t.com",
    // messagingSenderId: "683524",
    // appId: "1:683264069"
    apiKey: "AIzaSyBJly70pIuTRrdOOO5VdRDG_XAx9velfAk",
    authDomain: "cyclops-5acac.firebaseapp.com",
    projectId: "cyclops-5acac",
    storageBucket: "cyclops-5acac.appspot.com",
    messagingSenderId: "64143208674",
    appId: "1:64143208674:web:74d544637362fd208a6ebb",
    measurementId: "G-PTLFTJ8PGF"
  };
  
  const fire=firebase.initializeApp(firebaseConfig)
  
  const storage = firebase.storage()
  export  {
    fire,storage, firebase as default
  }
