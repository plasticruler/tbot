<template>
  <div>
    <table>
      <thead>
        <tr>
          <th>Entry Date</th>          
          <th>Text</th>
        </tr>
      </thead>
        <tr v-for="row in selflogs" v-bind:key="row.id">
          <td>{{row.created_date}}</td>          
          <td>{{row.message}}</td>
        </tr>
        <tr>      
    </table>
    
  </div>
</template>

<script>
import axios from 'axios';

axios.defaults.headers.common['username'] = 'xxx';
axios.defaults.headers.common['password'] = 'xxx';
axios.defaults.headers.common['Access-Control-Allow-Origin'] = '*';


export default {
  name: 'SelfLogs',
  data() {
    return {
      selflogs:[]
    };
  },
  methods:{      
      getData(){
          const path = 'http://192.168.0.9:5000/api/1.0/selflog/';
          axios.get(path)
          .then(res=>{
            console.log(res);
            this.selflogs = res.data.selflogs;
          })
          .catch(error=>{
              console.error(error);
          });
      },
  },
  created(){
      this.getData();
  },
};
</script>
