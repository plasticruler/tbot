<template>
  <div>
    <table>
      <thead>
        <tr>
          <th>Instrument</th>
          <th>JSE Code</th>
          <th>Tracking</th>
        </tr>
      </thead>
        <tr v-for="row in instruments.all" v-bind:key="row.jse_code">
          <td>{{row.company_name}}</td>
          <td>{{row.jse_code}}</td>
          <td><input type="checkbox" :id="row.jse_code" :value="row.jse_code" v-model="instruments.selected"></td>
        </tr>
        <tr>
          <td colspan="3">
              <button v-on:click="update()">Save</button>
          </td>
        </tr>
      
    </table>
    
  </div>
</template>

<script>
import axios from 'axios';

axios.defaults.headers.common['username'] = 'xxx';
axios.defaults.headers.common['password'] = 'xxx';
axios.defaults.headers.common['Access-Control-Allow-Origin'] = '*';


export default {
  name: 'Instruments',
  data() {
    return {
      instruments: {
        all:[],
        selected:[]
      }      
    };
  },
  methods:{
      update(){
        const path='http://192.168.0.9:5000/api/1.0/trackedinstrument/';
        let payload = this.instruments.selected.filter(x=>true).join(',');
        console.log('---');
        console.log(payload);
        console.log('****');
        axios.post(path, {'codes':payload})
          .then(res=>{
            console.log(res);
          })
          .catch(error=>{
            console.error(error);
          });
      },
      getMessage(){
          const path = 'http://192.168.0.9:5000/api/1.0/equityinstrument/';
          axios.get(path)
          .then(res=>{
            console.log(res);
            this.instruments.all = res.data.instruments;
            this.instruments.selected = res.data.instruments.filter(x=>{return x.is_active}).map(x=>x.jse_code);
          })
          .catch(error=>{
              console.error(error);
          });
      },
  },
  created(){
      this.getMessage();
  },
};
</script>
