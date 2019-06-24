/*
   Copyright (C) 2019  MAXS
   
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
'use strict';

odoo.define('website_sale_srenvio_delivery.checkout', function (require) {

    require('web.dom_ready');
    var ajax = require('web.ajax');

    /* Handle interactive carrier choice + cart update */
    var $pay_button = $('#o_payment_form_pay');
    /*
        TODO: Update parent  price label  when is changed shipping
     */
    var _onCarrierUpdateAnswer = function(result) {
        var $amount_delivery = $('#order_delivery span.oe_currency_value');
        var $amount_untaxed = $('#order_total_untaxed span.oe_currency_value');
        var $amount_tax = $('#order_total_taxes span.oe_currency_value');
        var $amount_total = $('#order_total span.oe_currency_value');
        var $carrier_badge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .badge.hidden');
        var $compute_badge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .o_delivery_compute');
        if (result.status === true) {
            $amount_delivery.text(result.new_amount_delivery);
            $amount_untaxed.text(result.new_amount_untaxed);
            $amount_tax.text(result.new_amount_tax);
            $amount_total.text(result.new_amount_total);
            $carrier_badge.children('span').text(result.new_amount_delivery);
            $carrier_badge.removeClass('hidden');
            $compute_badge.addClass('hidden');
            $pay_button.prop('disabled', false);
        }
        else {
            console.error(result.error_message);
            $compute_badge.text(result.error_message);
            $amount_delivery.text(result.new_amount_delivery);
            $amount_untaxed.text(result.new_amount_untaxed);
            $amount_tax.text(result.new_amount_tax);
            $amount_total.text(result.new_amount_total);
        } 
    };

    var _onSrenvioCarrierClick = function(ev) {
        $pay_button.prop('disabled', true);
        var subitem_id = $(ev.currentTarget).val();
        var subitem_id_split =  subitem_id.split("-");
        console.log(subitem_id)
        var values = {
            'carrier_id': subitem_id_split[0],
            'provider': subitem_id_split[1],
            'service_level_code': subitem_id_split[2]
        };
        ajax.jsonRpc('/shop/update_carrier', 'call', values).then(_onCarrierUpdateAnswer);
    };

    /* Render Shipments */
    var $carriers = $("#delivery_carrier input[name='delivery_type']");
    var dynamicSort = function (property) {
        var sortOrder = 1;
        if(property[0] === "-") {
            sortOrder = -1;
            property = property.substr(1);
        }
        return function (a,b) {
            /* next line works with strings and numbers, 
             * and you may want to customize it to your needs
             */
            var result = (a[property] < b[property]) ? -1 : (a[property] > b[property]) ? 1 : 0;
            return result * sortOrder;
        }
    }
    var dynamicSortMultiple = function () {
        /*
         * save the arguments object as it will be overwritten
         * note that arguments object is an array-like object
         * consisting of the names of the properties to sort by
         */
        var props = arguments;
        return function (obj1, obj2) {
            var i = 0, result = 0, numberOfProperties = props.length;
            /* try getting a different result from 0 (equal)
             * as long as we have extra properties to compare
             */
            while(result === 0 && i < numberOfProperties) {
                result = dynamicSort(props[i])(obj1, obj2);
                i++;
            }
            return result;
        }
    }
    var _onSrenvioShipmentsRender = function(result){
        qcount = result['qoutations'].length;
        carrier_id = result['carrier_id']
        if (result['status']){
            qoutations = result['qoutations'].sort(dynamicSortMultiple('days','total_pricing'))
        }else{
            qoutations = result['qoutations']
        }
        $( "#srenvio-list-group-subitem" ).empty();
        for( var i =0; i < qcount  ; i++ ){ 
            var shipment = qoutations[i];
            shipment_input = carrier_id +'-'+shipment['provider'] + '-' + shipment['service_level_code'] 
            shipment_label_for = carrier_id + "-" + i
            shipment_label = shipment['provider'] + " - " +shipment['service_level_name']
            $( "#srenvio-list-group-subitem" ).append( 
                " <li>" +
                " <input value='"+shipment_input+"' id='"+ shipment_input+"' " + 
                " type='radio'  name='srenvio_delivery_subtype' " +
                ///"checked="order.carrier_id and order.carrier_id.id == delivery.id and 'checked' or False " +
                " class=' " + (  qcount == 1 ?  'hidden' : '' ) + "' /> " +
                " <label class='label-optional' for='"+ shipment_label_for+"'>"+ shipment_label + " </label>"+
                " <span class='badge pull-right'>$&nbsp;<span class='oe_currency_value'>"+ shipment['total_pricing']+"</span></span>" +
                " <span class='badge pull-right'><span class='oe_currency_value'>"+ shipment['days']+"</span> Día(s)</span>" +
                " </li>"
             );
        }
        /* Set event onClik subitems*/
        var $srenvioCarriers = $("#srenvio-list-group-subitem input[name='srenvio_delivery_subtype']");
        $srenvioCarriers.click(_onSrenvioCarrierClick);

    };
    var _onSrenvioShipmentsClick = function(ev) {
        var carrier_id = $(ev.currentTarget).val();
        var values = {'carrier_id': carrier_id};
        ajax.jsonRpc('/shop/srenvio/shipments', 'call', values).then(_onSrenvioShipmentsRender);
    };
    var $carriers = $("#delivery_carrier input[name='delivery_type']");
    $carriers.click(_onSrenvioShipmentsClick);
    if ($carriers.length > 0) {
        $carriers.filter(':checked').click();
    }
});
