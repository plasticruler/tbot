Vue.component('ChatHistory', {
    props: ['chats'],
    template: "<div><chat-message " +
        "v-for='(chat,index) in chats.chat_history' :key='chat.chatid' " +
        ":message='chat' :last='index == chats.chat_history.length - 1'>" +
        "</chat-message></div>"        
});

Vue.component('ChatMessage', {
    props: ['message','last'],
    data: function () {
        return {
            lasts: this.$parent.$children[this.$parent.$children.length-1]===this,
            colors: {
                directions: {
                    0: '#167C33', //in
                    1: '#96a96a'  //out
                }
            }
        }
    },
    methods: {
        getColor(direction) {
            return this.colors['directions'][direction];
        }
    },
    template: "<div v-bind:style='{color:getColor(message.direction)}'>{{message.time}} - {{message.message}} {{message.direction==0?message.sender:''}} <div v-if='message.direction && last'><input type='text'></input><button>reply</button></div></div>"
});

var app = new Vue({
    el: '#app',
    methods: {

    },
    data: {
        message: 'Hello Vue.js!',
        chats: [{
                id: 0,
                first_name: 'Atrayu',
                chat_history: [{
                        direction: 1,
                        time: '201909311323',
                        message: 'how do i use the camera?',
                        sender: 'Snufkin',
                        chatid: 1223354,
                        messageid: 1
                    },
                    {
                        direction: 0,
                        time: '201909311323',
                        sender: 'Agent1',
                        message: 'hi how can i help you?',
                        chatid: 1223354,
                        messageid: 2
                    },
                    {
                        direction: 1,
                        time: '201909311323',
                        message: 'yea, thanks for reply. i was wondering does the camera encrypt its contents?',
                        sender: 'Snufkin',
                        chatid: 12231354,
                        messageid: 1
                    },
                ]
            },
            {
                id: 1,
                first_name: 'Artax',
                chat_history: [{
                        direction: 1,
                        time: '201909311323',
                        message: 'how do i use the cream?',
                        sender: 'Snufkin',
                        chatid: 1223354,
                        messageid: 1
                    },
                    {
                        direction: 0,
                        time: '201909311323',
                        sender: 'Agent1',
                        message: 'hi how can i help you?',
                        chatid: 1223354,
                        messageid: 2
                    },
                    {
                        direction: 1,
                        time: '201909311323',
                        sender: 'Agent1',
                        message: 'it stuck on me?',
                        chatid: 1223354,
                        messageid: 2
                    }
                ]
            },
            {
                id: 2,
                first_name: 'Greebo',
                chat_history: [{
                        direction: 1,
                        time: '201909311323',
                        message: 'how do i use the bangles??',
                        sender: 'Snufkin',
                        chatid: 1223354,
                        messageid: 1
                    },
                    {
                        direction: 0,
                        time: '201909311323',
                        sender: 'Agent1',
                        message: 'hi how can i help you?',
                        chatid: 1223354,
                        messageid: 2
                    }
                ]
            }
        ]
    },
    created: function () {
        console.log('application created.')
    }
})